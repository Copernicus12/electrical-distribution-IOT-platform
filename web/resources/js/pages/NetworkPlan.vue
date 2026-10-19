<script setup lang="ts">
import { Head } from '@inertiajs/vue3';
import { Box, Map as MapIcon } from '@lucide/vue';
import { ref } from 'vue';
import NetworkPlan3D from '@/components/NetworkPlan3D.vue';
import NetworkMap from '@/components/NetworkMap.vue';
import { networkPlan } from '@/routes';

const selected = ref('TR1');
const representation = ref<'3d' | 'map'>('map');
const supportVisible = ref(false);
defineOptions({
    layout: { breadcrumbs: [{ title: 'Network plan', href: networkPlan() }] },
});
</script>

<template>
    <Head title="Network plan" />
    <div class="flex min-w-0 flex-1 flex-col gap-5 p-4 md:p-6">
        <header class="flex flex-wrap items-start justify-between gap-3">
            <div>
                <h1 class="text-xl font-semibold tracking-tight">
                    Network plan
                </h1>
                <p class="mt-1 text-sm text-muted-foreground">
                    Explore the neighbourhood, from generation to each
                    residential connection.
                </p>
            </div>
            <span
                class="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-[11px] text-muted-foreground"
                ><span class="size-1.5 rounded-full bg-amber-500/80" /> Planning
                view</span
            >
        </header>
        <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="text-xs font-medium text-muted-foreground">
                Network representation
            </p>
            <div
                class="flex items-center gap-1 rounded-lg border border-border bg-muted/50 p-1"
                role="group"
                aria-label="Network representation"
            >
                <button
                    type="button"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    :class="
                        representation === '3d'
                            ? 'bg-background text-foreground shadow-xs'
                            : 'text-muted-foreground hover:text-foreground'
                    "
                    :aria-pressed="representation === '3d'"
                    @click="representation = '3d'"
                >
                    <Box class="size-3.5" aria-hidden="true" /> 3D view
                </button>
                <button
                    type="button"
                    class="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    :class="
                        representation === 'map'
                            ? 'bg-background text-foreground shadow-xs'
                            : 'text-muted-foreground hover:text-foreground'
                    "
                    :aria-pressed="representation === 'map'"
                    @click="representation = 'map'"
                >
                    <MapIcon class="size-3.5" aria-hidden="true" /> Map view
                </button>
            </div>
        </div>
        <NetworkPlan3D
            v-if="representation === '3d'"
            v-model:selected="selected"
            v-model:support-visible="supportVisible"
        />
        <NetworkMap
            v-else
            v-model:selected="selected"
            v-model:support-visible="supportVisible"
        />
        <p class="pb-1 text-[11px] leading-relaxed text-muted-foreground">
            Schematic layout based on the project topology. Positions and
            dwelling models are illustrative; equipment is not shown to scale.
        </p>
    </div>
</template>
