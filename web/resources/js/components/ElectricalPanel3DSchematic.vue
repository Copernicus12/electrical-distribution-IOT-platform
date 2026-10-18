<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue';
import type { ElectricalPanelScene } from '@/components/electrical-panel-3d/createElectricalPanelScene';

const props = defineProps<{ panelId: string }>();
const running = defineModel<boolean>('running', { default: false });
const panelLabel = computed(() => props.panelId);
const id = useId();
const viewport = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const rotation = ref(0);
const dragging = ref(false);
let model: ElectricalPanelScene | undefined;
let resizeObserver: ResizeObserver | undefined;
let themeObserver: MutationObserver | undefined;
let mounted = true;
let activePointer: number | null = null;
let startX = 0;
let startRotation = 0;

function rotateTo(yaw: number): void {
    let angle = Math.round(yaw) % 360;
    if (angle > 180) angle -= 360;
    if (angle < -180) angle += 360;
    rotation.value = angle;
    model?.rotate(rotation.value);
}

function startDrag(event: PointerEvent): void {
    if (!event.isPrimary || event.button !== 0 || loading.value || error.value)
        return;
    const stage = event.currentTarget as HTMLElement;
    stage.setPointerCapture(event.pointerId);
    stage.focus({ preventScroll: true });
    activePointer = event.pointerId;
    startX = event.clientX;
    startRotation = rotation.value;
    dragging.value = true;
}

function drag(event: PointerEvent): void {
    if (event.pointerId !== activePointer) return;
    rotateTo(startRotation + (event.clientX - startX) * 0.7);
}

function stopDrag(event: PointerEvent): void {
    if (event.pointerId !== activePointer) return;
    activePointer = null;
    dragging.value = false;
    const stage = event.currentTarget as HTMLElement;
    if (stage.hasPointerCapture(event.pointerId))
        stage.releasePointerCapture(event.pointerId);
}

function rotateWithKeyboard(event: KeyboardEvent): void {
    switch (event.key) {
        case 'ArrowLeft':
            rotateTo(rotation.value - 10);
            break;
        case 'ArrowRight':
            rotateTo(rotation.value + 10);
            break;
        case 'End':
            rotateTo(180);
            break;
        case 'Home':
        case 'Escape':
        case '0':
            rotateTo(0);
            break;
        default:
            return;
    }
    event.preventDefault();
}

function contextLost(event: Event): void {
    event.preventDefault();
    error.value =
        'The 3D view was interrupted. Wait for it to recover or reload the page.';
}

function contextRestored(): void {
    error.value = null;
    model?.resize();
}

onMounted(async () => {
    try {
        const { createElectricalPanelScene } =
            await import('@/components/electrical-panel-3d/createElectricalPanelScene');
        if (!mounted || !viewport.value) return;
        model = createElectricalPanelScene(viewport.value);
        model.setRunning(running.value);
        model.rotate(rotation.value);
        loading.value = false;
        resizeObserver = new ResizeObserver(() => model?.resize());
        resizeObserver.observe(viewport.value);
        themeObserver = new MutationObserver(() => model?.refreshTheme());
        themeObserver.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class'],
        });
        viewport.value.addEventListener('webglcontextlost', contextLost, true);
        viewport.value.addEventListener(
            'webglcontextrestored',
            contextRestored,
            true,
        );
    } catch {
        if (!mounted) return;
        loading.value = false;
        error.value =
            'The 3D model requires a browser with WebGL enabled. Enable hardware acceleration and reload the page.';
    }
});

watch(running, (value) => model?.setRunning(value));

onBeforeUnmount(() => {
    mounted = false;
    resizeObserver?.disconnect();
    themeObserver?.disconnect();
    viewport.value?.removeEventListener('webglcontextlost', contextLost, true);
    viewport.value?.removeEventListener(
        'webglcontextrestored',
        contextRestored,
        true,
    );
    model?.dispose();
});
</script>

<template>
    <article
        class="panel-schematic flex min-w-0 flex-col rounded-xl border border-sidebar-border/70 bg-card dark:border-sidebar-border"
        :aria-label="`Electrical panel ${panelId}`"
        :data-running="running"
    >
        <header class="flex items-center justify-between px-4 pt-4">
            <div>
                <h2 class="text-sm font-semibold tracking-wide">
                    {{ panelLabel }}
                </h2>
                <p class="mt-0.5 text-xs text-muted-foreground">
                    Electrical panel
                </p>
            </div>
            <span
                class="panel-indicator size-1.5 rounded-full"
                aria-hidden="true"
            />
        </header>
        <div
            class="panel-stage relative mx-1 mt-2 mb-1 aspect-[320/450] rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
            role="slider"
            tabindex="0"
            :aria-label="`3D rotation for ${panelLabel}`"
            :aria-valuemin="-180"
            :aria-valuemax="180"
            :aria-valuenow="rotation"
            :aria-valuetext="`${rotation} degrees`"
            :aria-describedby="`${id}-rotation-help`"
            :aria-busy="loading"
            aria-orientation="horizontal"
            :data-dragging="dragging"
            :data-renderer="!loading && !error ? 'webgl' : 'unavailable'"
            title="Drag left or right to rotate 360°. Double-click to reset the view."
            @pointerdown="startDrag"
            @pointermove="drag"
            @pointerup="stopDrag"
            @pointercancel="stopDrag"
            @lostpointercapture="stopDrag"
            @keydown="rotateWithKeyboard"
            @dblclick="rotateTo(0)"
        >
            <span :id="`${id}-rotation-help`" class="sr-only">
                3D model with an enclosure, doors, rails, terminals and wiring.
                Drag left or right to rotate 360° without tilting, or use the
                Left and Right arrow keys. Press End to view the back.
                Double-click or press Home or Escape to reset the view.
            </span>
            <div
                ref="viewport"
                class="pointer-events-none absolute inset-0 overflow-hidden rounded-lg"
            />
            <div
                v-if="loading || error"
                class="absolute inset-0 flex items-center justify-center px-6 text-center text-xs text-muted-foreground"
                role="status"
            >
                {{ error ?? 'Loading 3D model…' }}
            </div>
        </div>

        <footer
            class="mt-auto flex items-center justify-between gap-3 border-t border-sidebar-border/70 px-4 py-3 dark:border-sidebar-border"
        >
            <span class="text-xs text-muted-foreground">Panel process</span>
            <div class="flex items-center gap-2.5">
                <span
                    class="min-w-10 text-right text-xs font-medium"
                    :class="
                        running ? 'text-foreground' : 'text-muted-foreground'
                    "
                >
                    {{ running ? 'On' : 'Off' }}
                </span>
                <button
                    type="button"
                    role="switch"
                    :aria-checked="running"
                    :aria-label="`Panel process ${panelId}`"
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-border transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background motion-reduce:transition-none"
                    :class="running ? 'bg-primary' : 'bg-input'"
                    @click="running = !running"
                >
                    <span
                        aria-hidden="true"
                        class="pointer-events-none block size-4 rounded-full shadow-sm transition-transform motion-reduce:transition-none"
                        :class="
                            running
                                ? 'translate-x-4 bg-primary-foreground'
                                : 'translate-x-0.5 bg-foreground'
                        "
                    />
                </button>
            </div>
        </footer>
    </article>
</template>

<style scoped>
.panel-stage {
    cursor: grab;
    touch-action: pan-y;
    user-select: none;
}

.panel-stage[data-dragging='true'] {
    cursor: grabbing;
}

.panel-indicator {
    background: var(--muted-foreground);
}

.panel-schematic[data-running='true'] .panel-indicator {
    background: var(--chart-2);
}
</style>
