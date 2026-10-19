<script setup lang="ts">
import {
    Cable,
    House,
    Link2,
    Network,
    RotateCcw,
    Sun,
    UtilityPole,
    Zap,
    ZoomIn,
    ZoomOut,
} from '@lucide/vue';
import { computed, ref, useId } from 'vue';
import NetworkEquipmentInspector from '@/components/network-plan/NetworkEquipmentInspector.vue';
import {
    graphConnectionPath,
    graphNodeById,
    graphNodes,
    graphSize,
} from '@/components/network-plan/networkGraphLayout';
import {
    networkConnections,
    panelGroups,
} from '@/components/network-plan/networkTopology';
import type { AssetKind } from '@/components/network-plan/networkTopology';
import { Button } from '@/components/ui/button';

const selectedId = defineModel<string>('selected', { default: 'TR1' });
const supportVisible = defineModel<boolean>('supportVisible', {
    default: false,
});
const svg = ref<SVGSVGElement | null>(null);
const frame = ref({
    x: 0,
    y: 0,
    width: graphSize.width,
    height: graphSize.height,
});
const viewBox = computed(() =>
    [frame.value.x, frame.value.y, frame.value.width, frame.value.height].join(
        ' ',
    ),
);
const connections = computed(() =>
    networkConnections.filter(
        (connection) => !connection.normallyOpen || supportVisible.value,
    ),
);
const icons = {
    grid: UtilityPole,
    transformer: Zap,
    solar: Sun,
    bus: Cable,
    panel: Network,
    home: House,
};
const id = useId().replaceAll(':', '');
const nodeColors: Record<AssetKind, string> = {
    grid: 'text-cyan-600 dark:text-cyan-300',
    transformer: 'text-cyan-600 dark:text-cyan-300',
    solar: 'text-amber-600 dark:text-amber-300',
    bus: 'text-cyan-600 dark:text-cyan-300',
    panel: 'text-cyan-600 dark:text-cyan-300',
    home: 'text-emerald-700 dark:text-emerald-300',
};
let gesture: {
    pointer: number;
    x: number;
    y: number;
    frame: typeof frame.value;
    scale: number;
    moved: boolean;
} | null = null;
let wasDragged = false;

function select(value: string): void {
    selectedId.value = value;
}
function reset(): void {
    frame.value = { x: 0, y: 0, ...graphSize };
}
function zoom(factor: number, anchor?: { x: number; y: number }): void {
    const previous = frame.value;
    const width = Math.min(
        graphSize.width * 2,
        Math.max(240, previous.width * factor),
    );
    const ratio = width / previous.width;
    const point = anchor ?? {
        x: previous.x + previous.width / 2,
        y: previous.y + previous.height / 2,
    };
    frame.value = {
        x: point.x - (point.x - previous.x) * ratio,
        y: point.y - (point.y - previous.y) * ratio,
        width,
        height: previous.height * ratio,
    };
}
function focus(value: string): void {
    const node = graphNodeById.get(value);
    if (!node) return;
    const width = node.asset.kind === 'home' ? 360 : 620;
    const height = (width * graphSize.height) / graphSize.width;
    frame.value = {
        x: node.x - width / 2,
        y: node.y - height / 2,
        width,
        height,
    };
}
function wheel(event: WheelEvent): void {
    event.preventDefault();
    const matrix = svg.value?.getScreenCTM();
    if (!matrix || !svg.value) return;
    const point = svg.value.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const anchor = point.matrixTransform(matrix.inverse());
    zoom(event.deltaY > 0 ? 1.12 : 0.89, anchor);
}
function pointerDown(event: PointerEvent): void {
    if (!event.isPrimary || event.button !== 0 || !svg.value) return;
    const scale = svg.value.getScreenCTM()?.a;
    if (!scale) return;
    gesture = {
        pointer: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        frame: { ...frame.value },
        scale,
        moved: false,
    };
    wasDragged = false;
}
function pointerMove(event: PointerEvent): void {
    if (!gesture || event.pointerId !== gesture.pointer) return;
    const dx = event.clientX - gesture.x,
        dy = event.clientY - gesture.y;
    if (!gesture.moved && Math.hypot(dx, dy) < 5) return;
    gesture.moved = true;
    wasDragged = true;
    svg.value?.setPointerCapture(event.pointerId);
    frame.value = {
        ...gesture.frame,
        x: gesture.frame.x - dx / gesture.scale,
        y: gesture.frame.y - dy / gesture.scale,
    };
}
function pointerUp(event: PointerEvent): void {
    if (!gesture || event.pointerId !== gesture.pointer) return;
    if (svg.value?.hasPointerCapture(event.pointerId))
        svg.value.releasePointerCapture(event.pointerId);
    gesture = null;
}
function activate(value: string): void {
    if (!wasDragged) select(value);
}
function handleKey(event: KeyboardEvent): void {
    if (event.key === 'Home' || event.key === 'Escape') reset();
    else if (event.key === '+' || event.key === '=') zoom(0.8);
    else if (event.key === '-') zoom(1.25);
    else if (event.key === 'ArrowLeft')
        frame.value.x -= frame.value.width * 0.08;
    else if (event.key === 'ArrowRight')
        frame.value.x += frame.value.width * 0.08;
    else if (event.key === 'ArrowUp')
        frame.value.y -= frame.value.height * 0.08;
    else if (event.key === 'ArrowDown')
        frame.value.y += frame.value.height * 0.08;
    else return;
    event.preventDefault();
}
</script>

<template>
    <section
        class="min-w-0 overflow-hidden rounded-xl border border-sidebar-border/70 bg-card dark:border-sidebar-border"
        aria-label="Distribution network graph"
    >
        <div
            class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3"
        >
            <div class="flex items-center gap-2 text-sm font-medium">
                <Network
                    class="size-4 text-muted-foreground"
                    aria-hidden="true"
                />
                Network topology
                <span
                    class="rounded border border-border px-1.5 py-0.5 text-[10px] font-normal tracking-wide text-muted-foreground uppercase"
                    >Graph</span
                >
            </div>
            <Button
                size="sm"
                variant="outline"
                class="h-7 text-xs"
                :aria-pressed="supportVisible"
                @click="supportVisible = !supportVisible"
                ><Link2 class="size-3.5" aria-hidden="true" /> Support
                links</Button
            >
        </div>
        <div class="grid min-w-0 lg:grid-cols-[minmax(0,1fr)_260px]">
            <div class="relative min-w-0 bg-muted/15">
                <svg
                    ref="svg"
                    :viewBox="viewBox"
                    class="graph-stage block h-[460px] w-full touch-none outline-none select-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset sm:h-[570px] 2xl:h-[650px]"
                    role="group"
                    tabindex="0"
                    aria-label="Interactive electrical network graph"
                    :aria-describedby="id + '-graph-help'"
                    @wheel="wheel"
                    @pointerdown="pointerDown"
                    @pointermove="pointerMove"
                    @pointerup="pointerUp"
                    @pointercancel="pointerUp"
                    @keydown="handleKey"
                >
                    <title>
                        Electrical distribution graph: one transformer, two
                        solar installations, four panels and thirty apartments
                    </title>
                    <defs>
                        <pattern
                            :id="id + '-dots'"
                            width="24"
                            height="24"
                            patternUnits="userSpaceOnUse"
                        >
                            <circle
                                cx="1"
                                cy="1"
                                r="0.7"
                                class="fill-muted-foreground/15"
                            />
                        </pattern>
                        <marker
                            v-for="kind in ['supply', 'solar']"
                            :id="id + '-arrow-' + kind"
                            :key="kind"
                            viewBox="0 0 10 10"
                            refX="9"
                            refY="5"
                            markerWidth="6"
                            markerHeight="6"
                            orient="auto-start-reverse"
                        >
                            <path
                                d="M 1 1 L 9 5 L 1 9"
                                fill="none"
                                stroke="currentColor"
                                stroke-width="1.5"
                                :class="
                                    kind === 'solar'
                                        ? 'text-amber-600 dark:text-amber-300'
                                        : 'text-cyan-600 dark:text-cyan-300'
                                "
                            />
                        </marker>
                    </defs>
                    <rect
                        :x="frame.x"
                        :y="frame.y"
                        :width="frame.width"
                        :height="frame.height"
                        :fill="'url(#' + id + '-dots)'"
                    />
                    <g aria-hidden="true">
                        <g
                            v-for="(panel, index) in panelGroups"
                            :key="panel.id"
                        >
                            <rect
                                :x="[160, 430, 770, 1040][index] - 122"
                                y="606"
                                width="244"
                                height="284"
                                rx="16"
                                class="fill-background/30 stroke-border"
                                stroke-dasharray="4 6"
                            />
                            <text
                                :x="[160, 430, 770, 1040][index]"
                                y="625"
                                text-anchor="middle"
                                class="fill-muted-foreground text-[11px] tracking-wider"
                            >
                                {{ panel.id }} ·
                                {{ panel.apartments }} APARTMENTS
                            </text>
                        </g>
                    </g>
                    <g aria-label="Electrical connections">
                        <path
                            v-for="connection in connections"
                            :key="connection.id"
                            :data-connection-id="connection.id"
                            :data-kind="connection.kind"
                            :d="graphConnectionPath(connection)"
                            fill="none"
                            stroke="currentColor"
                            :stroke-width="
                                connection.from === selectedId ||
                                connection.to === selectedId
                                    ? 2.6
                                    : 1.7
                            "
                            :stroke-dasharray="
                                connection.normallyOpen ? '7 6' : undefined
                            "
                            :class="
                                connection.normallyOpen
                                    ? 'text-violet-500/80 dark:text-violet-300/70'
                                    : connection.kind === 'solar'
                                      ? 'text-amber-600/80 dark:text-amber-300/70'
                                      : connection.kind === 'residential'
                                        ? 'text-emerald-700/60 dark:text-emerald-300/45'
                                        : 'text-cyan-600/80 dark:text-cyan-300/70'
                            "
                            :marker-end="
                                connection.kind === 'supply' ||
                                connection.kind === 'solar'
                                    ? 'url(#' +
                                      id +
                                      '-arrow-' +
                                      connection.kind +
                                      ')'
                                    : undefined
                            "
                        >
                            <title>
                                {{ connection.from }} → {{ connection.to
                                }}{{
                                    connection.normallyOpen
                                        ? ' · normally open support link'
                                        : ''
                                }}
                            </title>
                        </path>
                    </g>
                    <g
                        v-for="node in graphNodes"
                        :key="node.asset.id"
                        :transform="'translate(' + node.x + ' ' + node.y + ')'"
                        role="button"
                        tabindex="0"
                        :aria-label="'Inspect ' + node.asset.name"
                        :aria-pressed="selectedId === node.asset.id"
                        :data-asset-id="node.asset.id"
                        class="graph-node cursor-pointer outline-none"
                        @click.stop="activate(node.asset.id)"
                        @keydown.enter.prevent.stop="select(node.asset.id)"
                        @keydown.space.prevent.stop="select(node.asset.id)"
                    >
                        <title>
                            {{ node.asset.name }} · {{ node.subtitle }}
                        </title>
                        <rect
                            :x="-node.width / 2"
                            :y="-node.height / 2"
                            :width="node.width"
                            :height="node.height"
                            :rx="node.asset.kind === 'home' ? 7 : 10"
                            class="fill-card transition-colors"
                            :class="
                                selectedId === node.asset.id
                                    ? 'stroke-amber-500'
                                    : 'stroke-border'
                            "
                            :stroke-width="
                                selectedId === node.asset.id ? 2.4 : 1.5
                            "
                        />
                        <component
                            :is="icons[node.asset.kind]"
                            :x="-node.width / 2 + 13"
                            :y="node.asset.kind === 'home' ? -8 : -10"
                            :width="node.asset.kind === 'home' ? 16 : 20"
                            :height="node.asset.kind === 'home' ? 16 : 20"
                            :class="nodeColors[node.asset.kind]"
                            aria-hidden="true"
                        />
                        <text
                            :x="node.asset.kind === 'home' ? 9 : 12"
                            :y="node.asset.kind === 'home' ? -1 : -3"
                            text-anchor="middle"
                            class="fill-foreground text-[13px] font-semibold tracking-wide"
                        >
                            {{ node.asset.id }}
                        </text>
                        <text
                            :x="node.asset.kind === 'home' ? 9 : 12"
                            :y="node.asset.kind === 'home' ? 13 : 15"
                            text-anchor="middle"
                            class="fill-muted-foreground text-[10px]"
                        >
                            {{ node.subtitle }}
                        </text>
                    </g>
                </svg>
                <div
                    class="pointer-events-none absolute top-4 left-4 text-[10px] tracking-widest text-muted-foreground uppercase"
                    aria-hidden="true"
                >
                    Design topology · {{ graphNodes.length }} nodes
                </div>
                <div
                    class="absolute right-3 bottom-3 flex items-center gap-1 rounded-lg border border-border bg-card/90 p-1 shadow-sm backdrop-blur-sm"
                    role="group"
                    aria-label="Graph zoom and reset controls"
                >
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Zoom in"
                        title="Zoom in"
                        @click="zoom(0.8)"
                        ><ZoomIn aria-hidden="true"
                    /></Button>
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Zoom out"
                        title="Zoom out"
                        @click="zoom(1.25)"
                        ><ZoomOut aria-hidden="true"
                    /></Button>
                    <div class="mx-1 h-4 w-px bg-border" />
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Reset view"
                        title="Reset view"
                        @click="reset"
                        ><RotateCcw aria-hidden="true"
                    /></Button>
                </div>
            </div>
            <NetworkEquipmentInspector
                v-model:selected="selectedId"
                @focus="focus"
            />
        </div>
        <div
            class="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3"
        >
            <div
                class="flex flex-wrap items-center gap-x-5 gap-y-2 text-[10px] text-muted-foreground"
                aria-label="Connection legend"
            >
                <span class="flex items-center gap-2"
                    ><span
                        class="h-0.5 w-5 bg-cyan-600/80 dark:bg-cyan-300/60"
                    />
                    Radial supply</span
                >
                <span class="flex items-center gap-2"
                    ><span
                        class="h-0.5 w-5 bg-amber-600/80 dark:bg-amber-300/60"
                    />
                    Solar generation</span
                >
                <span class="flex items-center gap-2"
                    ><span
                        class="h-0.5 w-5 bg-emerald-700/70 dark:bg-emerald-300/50"
                    />
                    Residential circuits</span
                >
                <span v-if="supportVisible" class="flex items-center gap-2"
                    ><span
                        class="w-5 border-t border-dashed border-violet-400"
                    />
                    Normally open</span
                >
            </div>
            <p
                :id="id + '-graph-help'"
                class="text-[10px] text-muted-foreground"
            >
                Drag or use arrow keys to pan · Scroll or +/− to zoom · Home to
                reset · Select a node to inspect
            </p>
        </div>
    </section>
</template>

<style scoped>
.graph-node:hover > rect,
.graph-node:focus-visible > rect {
    stroke: var(--ring);
    stroke-width: 2.4;
}
</style>
