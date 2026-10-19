<script setup lang="ts">
import {
    ArrowUpRight,
    Cable,
    House,
    Layers,
    Link2,
    MapPin,
    Network,
    RotateCcw,
    Search,
    Sun,
    UtilityPole,
    X,
    Zap,
    ZoomIn,
    ZoomOut,
} from '@lucide/vue';
import {
    computed,
    nextTick,
    onBeforeUnmount,
    onMounted,
    ref,
    useId,
    watch,
} from 'vue';
import NetworkEquipmentInspector from '@/components/network-plan/NetworkEquipmentInspector.vue';
import { supportLinkColor } from '@/components/network-plan/networkColors';
import {
    constrainMapFrame,
    mapZoomLimits,
} from '@/components/network-plan/mapViewport';
import type { MapFrame } from '@/components/network-plan/mapViewport';
import { rasterizeBasemap } from '@/components/network-plan/rasterizeBasemap';
import {
    buildingFootprints,
    canalPath,
    districts,
    localRoads,
    mainRoads,
    mapAssetById,
    mapAssets,
    mapBounds,
    mapConnectionPath,
    mapSize,
    riverPath,
} from '@/components/network-plan/neighbourhoodMap';
import {
    assetKindLabels,
    networkConnections,
} from '@/components/network-plan/networkTopology';

const selectedId = defineModel<string>('selected', { default: 'TR1' });
const supportVisible = defineModel<boolean>('supportVisible', {
    default: false,
});
const viewport = ref<HTMLDivElement | null>(null);
const svg = ref<SVGSVGElement | null>(null);
const basemapLayer = ref<SVGGElement | null>(null);
const basemapCanvas = ref<HTMLCanvasElement | null>(null);
const basemapReady = ref(false);
const popup = ref<HTMLElement | null>(null);
const query = ref('');
const showConnections = ref(false);
const popupOpen = ref(false);
const detailsOpen = ref(false);
const viewportSize = ref({ width: 1200, height: 720 });
const popupSize = ref({ width: 320, height: 270 });
const frame = ref({ x: 0, y: 0, width: mapSize.width, height: mapSize.height });
const id = useId().replaceAll(':', '');
const buildingFootprintPath = buildingFootprints.join(' ');
const icons = {
    grid: UtilityPole,
    transformer: Zap,
    solar: Sun,
    bus: Cable,
    panel: Zap,
    home: House,
};
const selected = computed(
    () => mapAssetById.get(selectedId.value) ?? mapAssetById.get('TR1')!,
);
const viewBox = computed(() =>
    [frame.value.x, frame.value.y, frame.value.width, frame.value.height].join(
        ' ',
    ),
);
const markerScale = computed(
    () => frame.value.width / viewportSize.value.width,
);
const zoomLevel = computed(() => mapSize.width / frame.value.width);
const zoomLimits = computed(() => mapZoomLimits(viewportSize.value, mapBounds));
const canZoomIn = computed(
    () => frame.value.width > zoomLimits.value.minimum + 0.01,
);
const canZoomOut = computed(
    () => frame.value.width < zoomLimits.value.maximum - 0.01,
);
const searchResults = computed(() => {
    const value = query.value.trim().toLowerCase();
    return value
        ? mapAssets
              .filter((entry) =>
                  [
                      entry.asset.id,
                      entry.asset.name,
                      assetKindLabels[entry.asset.kind],
                      entry.district,
                      entry.location,
                  ].some((text) => text.toLowerCase().includes(value)),
              )
              .slice(0, 8)
        : [];
});
const visibleConnections = computed(() =>
    networkConnections.filter(
        (connection) =>
            (!connection.normallyOpen || supportVisible.value) &&
            (showConnections.value ||
                (connection.normallyOpen && supportVisible.value) ||
                (popupOpen.value &&
                    (connection.from === selectedId.value ||
                        connection.to === selectedId.value))),
    ),
);
const popupStyle = computed(() => {
    const point = selected.value,
        rect = viewportSize.value;
    const x = ((point.x - frame.value.x) / frame.value.width) * rect.width;
    const y = ((point.y - frame.value.y) / frame.value.height) * rect.height;
    const width = Math.min(320, rect.width - 24);
    const preferLeft = x > rect.width * 0.55;
    const left = Math.max(
        12,
        Math.min(rect.width - width - 12, preferLeft ? x - width - 29 : x + 29),
    );
    const top = Math.max(
        rect.width < 640 ? 125 : 90,
        Math.min(rect.height - popupSize.value.height - 28, y - 54),
    );
    return {
        left: left + 'px',
        top: top + 'px',
        width: width + 'px',
        maxHeight: Math.max(180, rect.height - 120) + 'px',
    };
});
const selectedConnections = computed(() =>
    networkConnections.filter(
        (connection) =>
            connection.from === selectedId.value ||
            connection.to === selectedId.value,
    ),
);
let resizeObserver: ResizeObserver | undefined;
let popupObserver: ResizeObserver | undefined;
let gesture: {
    pointer: number;
    x: number;
    y: number;
    frame: typeof frame.value;
    scale: number;
} | null = null;
let wasDragged = false;
let disposed = false;
let wheelFrame = 0;
let wheelDelta = 0;
let wheelPoint = { x: 0, y: 0 };
let panFrame = 0;
let pendingPan: MapFrame | undefined;

function drawBasemap(): void {
    const canvas = basemapCanvas.value;
    if (!canvas || disposed) return;
    const scale = viewportSize.value.width / frame.value.width;
    canvas.style.transform =
        'translate3d(' +
        -frame.value.x * scale +
        'px,' +
        -frame.value.y * scale +
        'px,0) scale(' +
        scale +
        ')';
}
function flushPan(): void {
    panFrame = 0;
    if (!pendingPan) return;
    const next = pendingPan;
    pendingPan = undefined;
    setFrame(next);
}

function setFrame(value: MapFrame): void {
    frame.value = constrainMapFrame(value, viewportSize.value, mapBounds);
    drawBasemap();
}
function reset(): void {
    const width = zoomLimits.value.maximum;
    const height = width / zoomLimits.value.aspect;
    const centerX =
        viewportSize.value.width < 640 ? selected.value.x : mapSize.width / 2;
    setFrame({
        x: centerX - width / 2,
        y: (mapSize.height - height) / 2,
        width,
        height,
    });
}
function zoom(factor: number, anchor?: { x: number; y: number }): void {
    const previous = frame.value;
    const width = Math.max(
        zoomLimits.value.minimum,
        Math.min(zoomLimits.value.maximum, previous.width * factor),
    );
    const ratio = width / previous.width;
    const point = anchor ?? {
        x: previous.x + previous.width / 2,
        y: previous.y + previous.height / 2,
    };
    setFrame({
        x: point.x - (point.x - previous.x) * ratio,
        y: point.y - (point.y - previous.y) * ratio,
        width,
        height: previous.height * ratio,
    });
}
function focus(value: string): void {
    const point = mapAssetById.get(value);
    if (!point) return;
    const width = Math.min(900, Math.max(600, viewportSize.value.width));
    const height = width / zoomLimits.value.aspect;
    setFrame({
        x: point.x - width / 2,
        y: point.y - height / 2,
        width,
        height,
    });
}
function open(value: string, center = false): void {
    if (!mapAssetById.has(value)) return;
    selectedId.value = value;
    popupOpen.value = true;
    query.value = '';
    if (center) focus(value);
    void nextTick(() => popup.value?.focus({ preventScroll: true }));
}
function activate(value: string): void {
    if (!wasDragged) open(value);
}
function closePopup(): void {
    popupOpen.value = false;
    void nextTick(() =>
        svg.value
            ?.querySelector<SVGGElement>(
                '[data-asset-id="' + selectedId.value + '"]',
            )
            ?.focus({ preventScroll: true }),
    );
}
function wheel(event: WheelEvent): void {
    event.preventDefault();
    if (!svg.value) return;
    const unit =
        event.deltaMode === 1
            ? 16
            : event.deltaMode === 2
              ? viewportSize.value.height
              : 1;
    wheelDelta += event.deltaY * unit;
    wheelPoint = { x: event.clientX, y: event.clientY };
    if (wheelFrame) return;
    wheelFrame = requestAnimationFrame(() => {
        wheelFrame = 0;
        const delta = Math.max(-300, Math.min(300, wheelDelta));
        wheelDelta = 0;
        const matrix = svg.value?.getScreenCTM();
        if (!matrix || !svg.value || disposed) return;
        const point = svg.value.createSVGPoint();
        point.x = wheelPoint.x;
        point.y = wheelPoint.y;
        zoom(Math.exp(delta * 0.0015), point.matrixTransform(matrix.inverse()));
    });
}
function pointerDown(event: PointerEvent): void {
    if (!event.isPrimary || event.button !== 0) return;
    gesture = {
        pointer: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        frame: { ...frame.value },
        scale: svg.value?.getScreenCTM()?.a ?? 1,
    };
    wasDragged = false;
}
function pointerMove(event: PointerEvent): void {
    if (!gesture || event.pointerId !== gesture.pointer) return;
    const dx = event.clientX - gesture.x,
        dy = event.clientY - gesture.y;
    if (!wasDragged && Math.hypot(dx, dy) < 5) return;
    wasDragged = true;
    svg.value?.setPointerCapture(event.pointerId);
    pendingPan = {
        ...gesture.frame,
        x: gesture.frame.x - dx / gesture.scale,
        y: gesture.frame.y - dy / gesture.scale,
    };
    if (!panFrame) panFrame = requestAnimationFrame(flushPan);
}
function pointerUp(event: PointerEvent): void {
    if (!gesture || event.pointerId !== gesture.pointer) return;
    cancelAnimationFrame(panFrame);
    flushPan();
    if (svg.value?.hasPointerCapture(event.pointerId))
        svg.value.releasePointerCapture(event.pointerId);
    gesture = null;
}
function handleKey(event: KeyboardEvent): void {
    const next = { ...frame.value };
    if (event.key === 'Home') reset();
    else if (event.key === 'Escape') {
        popupOpen.value = false;
        detailsOpen.value = false;
    } else if (event.key === '+' || event.key === '=') zoom(0.8);
    else if (event.key === '-') zoom(1.25);
    else if (event.key === 'ArrowLeft') next.x -= next.width * 0.06;
    else if (event.key === 'ArrowRight') next.x += next.width * 0.06;
    else if (event.key === 'ArrowUp') next.y -= next.height * 0.06;
    else if (event.key === 'ArrowDown') next.y += next.height * 0.06;
    else return;
    if (event.key.startsWith('Arrow')) setFrame(next);
    event.preventDefault();
}
watch(supportVisible, (value) => {
    if (value) showConnections.value = true;
});
watch(selectedId, (value) => {
    popupOpen.value = true;
    const point = mapAssetById.get(value);
    if (
        point &&
        (point.x < frame.value.x ||
            point.x > frame.value.x + frame.value.width ||
            point.y < frame.value.y ||
            point.y > frame.value.y + frame.value.height)
    )
        focus(value);
});
watch(popup, (element) => {
    popupObserver?.disconnect();
    if (!element) return;
    popupObserver = new ResizeObserver(() => {
        const rect = element.getBoundingClientRect();
        popupSize.value = { width: rect.width, height: rect.height };
    });
    popupObserver.observe(element);
});
onMounted(() => {
    const layer = basemapLayer.value;
    if (layer) {
        void rasterizeBasemap(layer, mapSize.width, mapSize.height)
            .then((value) => {
                if (disposed) {
                    value.dispose();
                    return;
                }
                const canvas = basemapCanvas.value;
                try {
                    const context = canvas?.getContext('2d', { alpha: false });
                    if (!canvas || !context) return;
                    canvas.width = value.width;
                    canvas.height = value.height;
                    context.drawImage(value.image, 0, 0);
                    drawBasemap();
                    basemapReady.value = true;
                } finally {
                    value.dispose();
                }
            })
            .catch(() => {
                // The static SVG remains available if bitmap decoding is unsupported.
            });
    }
    let initialized = false;
    resizeObserver = new ResizeObserver(() => {
        if (!viewport.value) return;
        const rect = viewport.value.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        const centerY = frame.value.y + frame.value.height / 2;
        viewportSize.value = { width: rect.width, height: rect.height };
        const height = frame.value.width / zoomLimits.value.aspect;
        setFrame({ ...frame.value, y: centerY - height / 2, height });
        if (!initialized) {
            initialized = true;
            reset();
        }
    });
    if (viewport.value) resizeObserver.observe(viewport.value);
});
onBeforeUnmount(() => {
    disposed = true;
    cancelAnimationFrame(wheelFrame);
    cancelAnimationFrame(panFrame);
    if (basemapCanvas.value)
        basemapCanvas.value.width = basemapCanvas.value.height = 1;
    resizeObserver?.disconnect();
    popupObserver?.disconnect();
});
</script>

<template>
    <section
        class="neighbourhood-map overflow-hidden rounded-xl border border-sidebar-border/70"
        aria-label="Neighbourhood distribution map"
    >
        <div
            ref="viewport"
            class="map-viewport relative h-[620px] overflow-hidden sm:h-[720px] 2xl:h-[800px]"
            @keydown.esc="closePopup"
        >
            <canvas
                ref="basemapCanvas"
                data-basemap="cached"
                :data-ready="basemapReady"
                class="pointer-events-none absolute top-0 left-0 origin-top-left will-change-transform"
                :style="{
                    width: mapSize.width + 'px',
                    height: mapSize.height + 'px',
                }"
                aria-hidden="true"
            />
            <svg
                ref="svg"
                :viewBox="viewBox"
                class="map-stage relative block h-full w-full touch-none outline-none select-none focus-visible:ring-2 focus-visible:ring-[#d7bb7d] focus-visible:ring-inset"
                role="group"
                tabindex="0"
                aria-label="Interactive neighbourhood map. Drag to pan, scroll to zoom, and select an object for details."
                :aria-describedby="id + '-help'"
                @wheel="wheel"
                @pointerdown="pointerDown"
                @pointermove="pointerMove"
                @pointerup="pointerUp"
                @pointercancel="pointerUp"
                @keydown="handleKey"
                @click="!wasDragged && (popupOpen = false)"
            >
                <g
                    v-if="!basemapReady"
                    ref="basemapLayer"
                    data-basemap-vector="true"
                >
                    <defs>
                        <mask
                            :id="id + '-land'"
                            maskUnits="userSpaceOnUse"
                            x="0"
                            y="0"
                            :width="mapSize.width"
                            :height="mapSize.height"
                        >
                            <rect
                                x="-3000"
                                y="-3000"
                                width="8000"
                                height="8000"
                                fill="white"
                            />
                            <path
                                :d="riverPath"
                                fill="none"
                                stroke="black"
                                stroke-width="119"
                            />
                            <path
                                :d="canalPath"
                                fill="none"
                                stroke="black"
                                stroke-width="66"
                            />
                        </mask>
                        <mask
                            :id="id + '-water'"
                            maskUnits="userSpaceOnUse"
                            x="0"
                            y="0"
                            :width="mapSize.width"
                            :height="mapSize.height"
                        >
                            <rect
                                x="0"
                                y="0"
                                :width="mapSize.width"
                                :height="mapSize.height"
                                fill="black"
                            />
                            <path
                                :d="riverPath"
                                fill="none"
                                stroke="white"
                                stroke-width="122"
                                stroke-linecap="round"
                            />
                            <path
                                :d="canalPath"
                                fill="none"
                                stroke="white"
                                stroke-width="68"
                                stroke-linecap="round"
                            />
                        </mask>
                        <mask
                            :id="id + '-building-clearance'"
                            maskUnits="userSpaceOnUse"
                            x="0"
                            y="0"
                            :width="mapSize.width"
                            :height="mapSize.height"
                        >
                            <rect
                                x="0"
                                y="0"
                                :width="mapSize.width"
                                :height="mapSize.height"
                                fill="white"
                            />
                            <path
                                v-for="road in mainRoads"
                                :key="road.id"
                                :d="road.path"
                                fill="none"
                                stroke="black"
                                :stroke-width="road.width + 18"
                            />
                        </mask>
                        <path
                            v-for="road in mainRoads"
                            :id="id + '-' + road.id"
                            :key="road.id"
                            :d="road.path"
                        />
                    </defs>
                    <rect
                        x="-3000"
                        y="-3000"
                        width="8000"
                        height="8000"
                        fill="#17191a"
                    />
                    <g pointer-events="none" aria-hidden="true">
                        <g
                            data-layer="waterways"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path
                                :d="riverPath"
                                fill="none"
                                stroke="#292c2e"
                                stroke-width="122"
                            />
                            <path
                                :d="canalPath"
                                fill="none"
                                stroke="#292c2e"
                                stroke-width="68"
                            />
                            <path
                                :d="canalPath"
                                fill="none"
                                stroke="#090b0c"
                                stroke-width="60"
                            />
                            <path
                                :d="riverPath"
                                fill="none"
                                stroke="#090b0c"
                                stroke-width="114"
                            />
                        </g>
                        <g :mask="'url(#' + id + '-land)'">
                            <path
                                :d="buildingFootprintPath"
                                :mask="'url(#' + id + '-building-clearance)'"
                                data-layer="buildings"
                                fill="#1c1f20"
                                stroke="#2a2d2f"
                                stroke-width="0.8"
                            />
                            <path
                                v-for="(road, index) in localRoads"
                                :key="index"
                                :d="road"
                                fill="none"
                                stroke="#2c2f31"
                                stroke-width="2.3"
                            />
                        </g>
                        <g
                            v-for="road in mainRoads"
                            :key="road.id"
                            :data-road-id="road.id"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path
                                :d="road.path"
                                fill="none"
                                stroke="#393c3e"
                                :stroke-width="road.width + 4"
                            />
                            <path
                                :d="road.path"
                                fill="none"
                                stroke="#272a2c"
                                :stroke-width="road.width"
                            />
                        </g>
                        <g
                            :mask="'url(#' + id + '-water)'"
                            data-layer="bridges"
                        >
                            <g
                                v-for="road in mainRoads"
                                :key="road.id"
                                :data-bridge-road-id="road.id"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            >
                                <path
                                    :d="road.path"
                                    fill="none"
                                    stroke="#505557"
                                    :stroke-width="road.width + 6"
                                />
                                <path
                                    :d="road.path"
                                    fill="none"
                                    stroke="#2c2f31"
                                    :stroke-width="road.width"
                                />
                            </g>
                        </g>
                        <text
                            v-for="district in districts"
                            :key="district.id"
                            :x="district.labelX"
                            :y="district.labelY"
                            text-anchor="middle"
                            class="district-label"
                        >
                            {{ district.name.toUpperCase() }}
                        </text>
                        <text
                            v-for="(road, index) in mainRoads"
                            :key="'label-' + road.id"
                            class="street-label"
                        >
                            <textPath
                                :href="'#' + id + '-' + road.id"
                                :startOffset="index % 2 ? '62%' : '29%'"
                            >
                                {{ road.name }}
                            </textPath>
                        </text>
                        <text
                            x="930"
                            y="460"
                            transform="rotate(-65 930 460)"
                            class="water-label"
                        >
                            River Alder
                        </text>
                        <text
                            x="520"
                            y="632"
                            transform="rotate(8 520 632)"
                            class="water-label"
                        >
                            Mill Canal
                        </text>
                    </g>
                </g>
                <rect
                    x="0"
                    y="0"
                    :width="mapSize.width"
                    :height="mapSize.height"
                    fill="transparent"
                />
                <g aria-label="Electrical connections" pointer-events="none">
                    <path
                        v-for="connection in visibleConnections"
                        :key="connection.id"
                        :d="mapConnectionPath(connection)"
                        :data-connection-id="connection.id"
                        :data-kind="connection.kind"
                        fill="none"
                        :stroke="
                            connection.normallyOpen
                                ? supportLinkColor
                                : connection.from === selectedId ||
                                    connection.to === selectedId
                                  ? '#c9ac73'
                                  : '#777a77'
                        "
                        :stroke-width="
                            markerScale *
                            (connection.from === selectedId ||
                            connection.to === selectedId
                                ? 1.6
                                : 1)
                        "
                        :stroke-dasharray="
                            connection.normallyOpen
                                ? 5 * markerScale + ' ' + 6 * markerScale
                                : undefined
                        "
                        :opacity="
                            connection.normallyOpen
                                ? 0.8
                                : connection.from === selectedId ||
                                    connection.to === selectedId
                                  ? 0.7
                                  : 0.35
                        "
                    />
                </g>
                <g
                    v-for="entry in mapAssets"
                    :key="entry.asset.id"
                    :transform="'translate(' + entry.x + ' ' + entry.y + ')'"
                    role="button"
                    tabindex="0"
                    :aria-label="'Inspect ' + entry.asset.name"
                    :aria-pressed="selectedId === entry.asset.id && popupOpen"
                    :data-asset-id="entry.asset.id"
                    class="map-marker cursor-pointer outline-none"
                    @click.stop="activate(entry.asset.id)"
                    @keydown.enter.prevent.stop="open(entry.asset.id)"
                    @keydown.space.prevent.stop="open(entry.asset.id)"
                >
                    <title>{{ entry.asset.name }} · {{ entry.location }}</title>
                    <g :transform="'scale(' + markerScale + ')'">
                        <circle r="26" fill="transparent" />
                        <circle
                            v-if="selectedId === entry.asset.id && popupOpen"
                            r="26"
                            fill="#d9bd7c"
                            fill-opacity="0.13"
                            stroke="#d9bd7c"
                            stroke-opacity="0.35"
                            stroke-width="5"
                        />
                        <circle
                            :r="
                                entry.asset.kind === 'home'
                                    ? 11
                                    : entry.asset.kind === 'bus'
                                      ? 12
                                      : 18
                            "
                            fill="#1b1e1f"
                            :stroke="
                                selectedId === entry.asset.id && popupOpen
                                    ? '#e1c383'
                                    : entry.asset.kind === 'solar'
                                      ? '#d5cb82'
                                      : '#65696a'
                            "
                            :stroke-width="
                                entry.asset.kind === 'home' ? 1.7 : 2.5
                            "
                        />
                        <component
                            :is="icons[entry.asset.kind]"
                            :x="entry.asset.kind === 'home' ? -5 : -8"
                            :y="entry.asset.kind === 'home' ? -5 : -8"
                            :width="entry.asset.kind === 'home' ? 10 : 16"
                            :height="entry.asset.kind === 'home' ? 10 : 16"
                            :color="
                                entry.asset.kind === 'solar'
                                    ? '#e5dd9d'
                                    : '#d7d9d8'
                            "
                            :fill="
                                entry.asset.kind === 'panel'
                                    ? '#d7d9d8'
                                    : 'none'
                            "
                            aria-hidden="true"
                        />
                        <g
                            v-if="
                                (entry.asset.kind !== 'home' &&
                                    entry.asset.kind !== 'bus') ||
                                zoomLevel > 1.5 ||
                                (selectedId === entry.asset.id && popupOpen)
                            "
                            transform="translate(0 29)"
                        >
                            <rect
                                x="-21"
                                y="-8"
                                width="42"
                                height="17"
                                rx="4"
                                fill="#141617"
                                fill-opacity="0.88"
                            />
                            <text
                                text-anchor="middle"
                                y="3"
                                fill="#b8bcb9"
                                font-size="9"
                                font-weight="500"
                                letter-spacing="0.7"
                            >
                                {{ entry.asset.id }}
                            </text>
                        </g>
                    </g>
                </g>
            </svg>

            <div
                class="map-topbar pointer-events-none absolute inset-x-4 top-4 flex flex-wrap items-start justify-between gap-2 sm:inset-x-5 sm:top-5"
            >
                <div class="pointer-events-auto relative w-full sm:w-[350px]">
                    <div
                        class="map-search flex h-11 items-center gap-2 rounded-lg px-3 shadow-lg"
                    >
                        <Search
                            class="size-4 shrink-0 text-[#858b8c]"
                            aria-hidden="true"
                        />
                        <input
                            v-model="query"
                            type="search"
                            class="min-w-0 flex-1 bg-transparent text-xs text-[#d9dcda] outline-none placeholder:text-[#808687]"
                            placeholder="Search panels, homes or generation…"
                            aria-label="Search network"
                            :aria-controls="
                                query ? id + '-search-results' : undefined
                            "
                            @keydown.enter.prevent="
                                searchResults[0] &&
                                open(searchResults[0].asset.id, true)
                            "
                            @keydown.esc.stop="query = ''"
                        />
                        <span
                            class="rounded border border-[#343839] px-1.5 py-0.5 text-[9px] text-[#7b8181]"
                            >40</span
                        >
                    </div>
                    <div
                        v-if="query.trim()"
                        :id="id + '-search-results'"
                        class="map-search mt-2 max-h-80 overflow-auto rounded-lg p-1.5 shadow-xl"
                        aria-label="Search results"
                    >
                        <button
                            v-for="entry in searchResults"
                            :key="entry.asset.id"
                            type="button"
                            class="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left hover:bg-[#2a2e2e] focus-visible:outline-2 focus-visible:outline-[#d6b97d]"
                            @click="open(entry.asset.id, true)"
                        >
                            <component
                                :is="icons[entry.asset.kind]"
                                class="size-4 shrink-0 text-[#b3b5ad]"
                                aria-hidden="true"
                            />
                            <span class="min-w-0"
                                ><span
                                    class="block text-xs font-medium text-[#d9dcda]"
                                    >{{ entry.asset.name }}</span
                                ><span
                                    class="block truncate text-[10px] text-[#878e8c]"
                                    >{{ entry.location }}</span
                                ></span
                            >
                        </button>
                        <p
                            v-if="!searchResults.length"
                            class="px-3 py-4 text-xs text-[#969b98]"
                        >
                            No matching equipment.
                        </p>
                    </div>
                </div>
                <div class="pointer-events-auto flex items-center gap-1.5">
                    <button
                        type="button"
                        class="map-tool flex h-9 items-center gap-1.5 rounded-md px-2.5 text-[10px]"
                        :aria-pressed="showConnections"
                        @click="showConnections = !showConnections"
                    >
                        <Layers class="size-3.5" aria-hidden="true" />
                        Connections
                    </button>
                    <button
                        type="button"
                        class="map-tool flex h-9 items-center gap-1.5 rounded-md px-2.5 text-[10px]"
                        :aria-pressed="supportVisible"
                        data-support="true"
                        @click="supportVisible = !supportVisible"
                    >
                        <Link2 class="size-3.5" aria-hidden="true" /> Support
                        links
                    </button>
                </div>
            </div>

            <article
                v-if="popupOpen"
                ref="popup"
                role="dialog"
                tabindex="-1"
                :aria-labelledby="id + '-popup-title'"
                class="map-popup absolute z-10 overflow-auto rounded-xl p-5 outline-none"
                :style="popupStyle"
                @keydown.esc.stop="closePopup"
            >
                <div class="flex items-center justify-between gap-3">
                    <div
                        class="flex min-w-0 items-center gap-2 rounded-full bg-[#262929] px-3 py-1.5"
                    >
                        <h2
                            :id="id + '-popup-title'"
                            class="text-sm font-semibold tracking-wide text-[#e1e3df]"
                        >
                            {{ selected.asset.id }}
                        </h2>
                        <span
                            class="size-1.5 rounded-full bg-[#d6be83]"
                            aria-hidden="true"
                        />
                    </div>
                    <div class="flex items-center gap-2">
                        <span
                            class="rounded-full border border-[#3b3e3f] px-2 py-1 text-[9px] text-[#b9bebe]"
                            >{{
                                selected.asset.kind === 'home'
                                    ? selected.asset.panelId
                                    : selected.asset.kind === 'panel'
                                      ? 'PM3255'
                                      : selected.asset.kind === 'solar'
                                        ? 'PV'
                                        : selected.asset.kind === 'transformer'
                                          ? 'MV / LV'
                                          : selected.asset.kind === 'grid'
                                            ? '20 kV'
                                            : '400 V'
                            }}</span
                        >
                        <button
                            type="button"
                            class="rounded p-1 text-[#969c9e] hover:bg-[#2b2e2f] hover:text-white focus-visible:outline-2 focus-visible:outline-[#d6b97d]"
                            aria-label="Close popup"
                            @click="closePopup"
                        >
                            <X class="size-3.5" aria-hidden="true" />
                        </button>
                    </div>
                </div>
                <p class="mt-3 text-xs font-medium text-[#c5c9c9]">
                    {{ assetKindLabels[selected.asset.kind] }}
                </p>
                <p
                    class="mt-1.5 flex items-start gap-2 text-[11px] leading-relaxed text-[#9ba1a2]"
                >
                    <MapPin
                        class="mt-0.5 size-3.5 shrink-0"
                        aria-hidden="true"
                    />{{ selected.location }}
                </p>
                <dl class="mt-5 grid grid-cols-2 gap-x-3 gap-y-4">
                    <div
                        v-for="spec in selected.asset.specifications.slice(
                            0,
                            2,
                        )"
                        :key="spec.label"
                    >
                        <dt class="text-[10px] text-[#8b9092]">
                            {{ spec.label }}
                        </dt>
                        <dd class="mt-0.5 text-sm font-semibold text-[#e0e3e3]">
                            {{ spec.value }}
                        </dd>
                    </div>
                </dl>
                <div
                    class="mt-5 flex items-center justify-between gap-3 border-t border-[#343839] pt-3"
                >
                    <span class="text-[10px] text-[#92999b]"
                        >{{ selectedConnections.length }} connections · Design
                        data</span
                    >
                    <button
                        type="button"
                        class="flex items-center gap-1.5 rounded text-[10px] font-medium text-[#d8c08b] hover:text-white focus-visible:outline-2 focus-visible:outline-[#d6b97d]"
                        @click="detailsOpen = true"
                    >
                        Details
                        <ArrowUpRight class="size-3.5" aria-hidden="true" />
                    </button>
                </div>
            </article>

            <div
                v-if="detailsOpen"
                @keydown.esc.stop="detailsOpen = false"
                class="map-details absolute inset-y-4 right-4 z-20 w-[min(280px,calc(100%-32px))] overflow-auto rounded-xl border border-[#3b3e40] bg-[#191b1c] shadow-2xl"
            >
                <div
                    class="sticky top-0 z-10 flex items-center justify-between border-b border-[#34383a] bg-[#191b1c] px-4 py-3"
                >
                    <span class="text-xs font-medium text-[#d9dede]"
                        >Equipment details</span
                    ><button
                        type="button"
                        class="rounded p-1 text-[#a2aaac] focus-visible:outline-2 focus-visible:outline-[#d6b97d]"
                        aria-label="Close equipment details"
                        @click="detailsOpen = false"
                    >
                        <X class="size-4" aria-hidden="true" />
                    </button>
                </div>
                <NetworkEquipmentInspector
                    v-model:selected="selectedId"
                    @focus="focus"
                />
            </div>
            <div
                class="pointer-events-none absolute bottom-5 left-5 hidden items-center gap-4 text-[10px] text-[#969d98] sm:flex"
                aria-label="Map legend"
            >
                <span class="flex items-center gap-1.5"
                    ><Zap class="size-3.5" aria-hidden="true" /> Panels</span
                ><span class="flex items-center gap-1.5"
                    ><Sun class="size-3.5 text-[#d6cc85]" aria-hidden="true" />
                    Solar</span
                ><span class="flex items-center gap-1.5"
                    ><House class="size-3.5" aria-hidden="true" /> Homes</span
                >
            </div>
            <div
                class="absolute right-4 bottom-4 flex items-center gap-1 rounded-lg border border-[#3b3e3e] bg-[#1a1d1d]/95 p-1.5 shadow-xl"
                role="group"
                aria-label="Map zoom and reset controls"
            >
                <button
                    type="button"
                    class="map-control"
                    :disabled="!canZoomIn"
                    aria-label="Zoom in"
                    title="Zoom in"
                    @click="zoom(0.8)"
                >
                    <ZoomIn class="size-4" aria-hidden="true" />
                </button>
                <button
                    type="button"
                    class="map-control"
                    :disabled="!canZoomOut"
                    aria-label="Zoom out"
                    title="Zoom out"
                    @click="zoom(1.25)"
                >
                    <ZoomOut class="size-4" aria-hidden="true" />
                </button>
                <div class="mx-1 h-4 w-px bg-[#3b3e3e]" />
                <button
                    type="button"
                    class="map-control"
                    aria-label="Reset map"
                    title="Reset map"
                    @click="reset"
                >
                    <RotateCcw class="size-4" aria-hidden="true" />
                </button>
            </div>
        </div>
        <footer
            class="flex flex-wrap items-center justify-between gap-2 border-t border-[#2e3231] bg-[#171a1b] px-4 py-3 text-[10px] text-[#8b938c]"
        >
            <span class="flex items-center gap-2"
                ><Network class="size-3" aria-hidden="true" /> 4 districts · 30
                residential units · 2 solar installations</span
            ><span :id="id + '-help'"
                >Illustrative map · Drag to pan · Scroll to zoom · Click to
                inspect</span
            >
        </footer>
    </section>
</template>

<style scoped>
.neighbourhood-map {
    color-scheme: dark;
    background: #17191a;
}
.map-stage {
    cursor: grab;
}
.map-stage:active {
    cursor: grabbing;
}
.district-label {
    fill: #5b6261;
    font-size: 19px;
    font-weight: 500;
    letter-spacing: 4px;
}
.street-label {
    fill: #767e7b;
    font-size: 13px;
    paint-order: stroke;
    stroke: #1b1e1f;
    stroke-width: 4px;
}
.water-label {
    fill: #404948;
    font-size: 18px;
    font-style: italic;
    letter-spacing: 2px;
}
.map-search {
    border: 1px solid #3b403d;
    background: #1b1e1f;
}
.map-tool {
    border: 1px solid #3b403d;
    background: #1b1e1fef;
    color: #afb6ac;
}
.map-tool:hover,
.map-tool[aria-pressed='true'] {
    color: #dfc58d;
    border-color: #a28d62;
}
.map-tool[data-support='true'][aria-pressed='true'] {
    color: #bdaddd;
    border-color: v-bind(supportLinkColor);
}
.map-tool:focus-visible,
.map-control:focus-visible {
    outline: 2px solid #d6b97d;
    outline-offset: 2px;
}
.map-control {
    display: flex;
    width: 30px;
    height: 30px;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    color: #c7cdc5;
}
.map-control:disabled {
    opacity: 0.35;
    cursor: not-allowed;
}
.map-control:hover:not(:disabled) {
    background: #303536;
    color: #ebddbb;
}
.map-popup {
    border: 1px solid #e2c17d;
    background: #191b1b;
    box-shadow:
        0 0 0 4px #d4b97830,
        0 0 0 5px #d4b97845,
        0 14px 48px #0009;
}
.map-marker:hover circle,
.map-marker:focus-visible circle {
    stroke: #e4c27e;
}
.map-details {
    --background: #191b1c;
    --foreground: #d7dede;
    --muted-foreground: #939d9e;
    --border: #343a3c;
    --input: #3d4446;
    --accent: #2c3234;
    --sidebar-border: #343a3c;
    --ring: #d6b97d;
}
</style>
