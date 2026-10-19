<script setup lang="ts">
import { Box, Link2, RotateCcw, ZoomIn, ZoomOut } from '@lucide/vue';
import {
    computed,
    onBeforeUnmount,
    onMounted,
    ref,
    shallowRef,
    useId,
    watch,
} from 'vue';
import type {
    NetworkScene,
    PlanView,
    ProjectedLabel,
} from '@/components/network-plan/createNetworkScene';
import NetworkEquipmentInspector from '@/components/network-plan/NetworkEquipmentInspector.vue';
import { assetById } from '@/components/network-plan/networkTopology';
import { Button } from '@/components/ui/button';

const selectedId = defineModel<string>('selected', { default: 'TR1' });
const viewport = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const view = ref<PlanView>('perspective');
const supportVisible = defineModel<boolean>('supportVisible', {
    default: false,
});
const labels = shallowRef<ProjectedLabel[]>([]);
const visibleLabels = computed(() =>
    labels.value.filter((label) => {
        const asset = assetById.get(label.id)!;
        return (
            label.visible &&
            (['grid', 'transformer', 'solar', 'panel'].includes(asset.kind) ||
                asset.id === selectedId.value)
        );
    }),
);
const views: { id: PlanView; label: string }[] = [
    { id: 'perspective', label: 'Perspective' },
    { id: 'top', label: 'Top' },
    { id: 'front', label: 'Front' },
];
const id = useId();
let model: NetworkScene | undefined;
let resizeObserver: ResizeObserver | undefined;
let themeObserver: MutationObserver | undefined;
let mounted = true;

function select(id: string): void {
    selectedId.value = id;
}
function setView(value: PlanView): void {
    view.value = value;
    model?.setView(value);
}
function reset(): void {
    setView('perspective');
}
function contextLost(): void {
    error.value =
        'The 3D view was interrupted. Wait for it to recover or reload the page.';
}
function contextRestored(): void {
    error.value = null;
}
watch(selectedId, (value) => model?.select(value));
watch(supportVisible, (value) => model?.showSupport(value));

onMounted(async () => {
    try {
        const { createNetworkScene } =
            await import('@/components/network-plan/createNetworkScene');
        if (!mounted || !viewport.value) return;
        model = createNetworkScene(viewport.value, {
            onSelect: select,
            onProject: (value) => {
                labels.value = value;
            },
        });
        model.select(selectedId.value);
        model.showSupport(supportVisible.value);
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
        model?.dispose();
        loading.value = false;
        error.value =
            'The 3D plan requires WebGL. Enable hardware acceleration in your browser and reload the page.';
    }
});

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
    <section
        class="min-w-0 overflow-hidden rounded-xl border border-sidebar-border/70 bg-card dark:border-sidebar-border"
        aria-label="Interactive distribution network plan"
    >
        <div
            class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3"
        >
            <div class="flex items-center gap-2 text-sm font-medium">
                <Box class="size-4 text-muted-foreground" aria-hidden="true" />
                Site overview
                <span
                    class="rounded border border-border px-1.5 py-0.5 text-[10px] font-normal tracking-wide text-muted-foreground uppercase"
                    >3D</span
                >
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <div
                    class="flex items-center gap-0.5 rounded-md bg-muted p-0.5"
                    role="group"
                    aria-label="Camera view"
                >
                    <button
                        v-for="option in views"
                        :key="option.id"
                        type="button"
                        class="rounded px-2.5 py-1 text-xs transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        :class="
                            view === option.id
                                ? 'bg-background text-foreground shadow-xs'
                                : 'text-muted-foreground hover:text-foreground'
                        "
                        :aria-pressed="view === option.id"
                        :disabled="loading || !!error"
                        @click="setView(option.id)"
                    >
                        {{ option.label }}
                    </button>
                </div>
                <Button
                    size="sm"
                    variant="outline"
                    class="h-7 text-xs"
                    :aria-pressed="supportVisible"
                    :disabled="loading || !!error"
                    @click="supportVisible = !supportVisible"
                >
                    <Link2 class="size-3.5" aria-hidden="true" /> Support links
                </Button>
            </div>
        </div>
        <div class="grid min-w-0 lg:grid-cols-[minmax(0,1fr)_260px]">
            <div class="relative min-w-0 bg-muted/15">
                <div
                    class="network-stage relative h-[460px] outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset sm:h-[570px] 2xl:h-[650px]"
                    role="region"
                    tabindex="0"
                    aria-label="3D neighbourhood network. Use arrow keys to rotate, plus or minus to zoom, and Home to reset."
                    :aria-describedby="id + '-controls'"
                    :aria-busy="loading"
                    :data-renderer="
                        !loading && !error ? 'webgl' : 'unavailable'
                    "
                    @keydown="model?.handleKey($event)"
                >
                    <div
                        ref="viewport"
                        class="absolute inset-0 overflow-hidden"
                    />
                    <div
                        v-if="!loading && !error"
                        class="pointer-events-none absolute inset-0 overflow-hidden"
                        aria-label="Equipment labels"
                    >
                        <button
                            v-for="label in visibleLabels"
                            :key="label.id"
                            type="button"
                            class="pointer-events-auto absolute flex -translate-x-1/2 -translate-y-full items-center gap-1.5 rounded border bg-card/90 px-2 py-1 text-[10px] shadow-sm backdrop-blur-sm transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            :class="
                                selectedId === label.id
                                    ? 'border-amber-500/60 text-foreground'
                                    : 'hidden border-border/80 text-muted-foreground hover:text-foreground sm:flex'
                            "
                            :style="{
                                left: label.x + 'px',
                                top: label.y + 'px',
                            }"
                            :aria-label="
                                'Select ' + assetById.get(label.id)?.name
                            "
                            :aria-pressed="selectedId === label.id"
                            @click.stop="select(label.id)"
                        >
                            <span
                                class="size-1 rounded-full"
                                :class="
                                    assetById.get(label.id)?.kind === 'solar'
                                        ? 'bg-amber-400'
                                        : 'bg-cyan-500/70'
                                "
                                aria-hidden="true"
                            />
                            <span class="font-semibold tracking-wide">{{
                                label.id
                            }}</span>
                            <span>{{
                                assetById.get(label.id)?.specifications[0].value
                            }}</span>
                        </button>
                    </div>
                    <div
                        v-if="loading || error"
                        class="absolute inset-0 flex items-center justify-center bg-card/80 p-8 text-center text-sm text-muted-foreground"
                        role="status"
                    >
                        {{ error ?? 'Building the 3D network…' }}
                    </div>
                </div>
                <div
                    class="pointer-events-none absolute top-4 left-4 flex items-center gap-1.5 text-[10px] tracking-widest text-muted-foreground uppercase"
                    aria-hidden="true"
                >
                    <span class="size-1 rounded-full bg-muted-foreground" />
                    Design topology
                </div>
                <div
                    class="absolute right-3 bottom-3 flex items-center gap-1 rounded-lg border border-border bg-card/90 p-1 shadow-sm backdrop-blur-sm"
                    role="group"
                    aria-label="Zoom and reset controls"
                >
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Zoom in"
                        title="Zoom in"
                        :disabled="loading || !!error"
                        @click="model?.zoom(0.8)"
                        ><ZoomIn aria-hidden="true"
                    /></Button>
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Zoom out"
                        title="Zoom out"
                        :disabled="loading || !!error"
                        @click="model?.zoom(1.25)"
                        ><ZoomOut aria-hidden="true"
                    /></Button>
                    <div class="mx-1 h-4 w-px bg-border" />
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        aria-label="Reset view"
                        title="Reset view"
                        :disabled="loading || !!error"
                        @click="reset"
                        ><RotateCcw aria-hidden="true"
                    /></Button>
                </div>
            </div>
            <NetworkEquipmentInspector
                v-model:selected="selectedId"
                :focus-disabled="loading || !!error"
                @focus="model?.focus($event)"
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
            <p :id="id + '-controls'" class="text-[10px] text-muted-foreground">
                Drag to orbit · Scroll to zoom · Right-drag to pan · Click to
                inspect
            </p>
        </div>
    </section>
</template>
