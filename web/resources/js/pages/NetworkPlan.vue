<script setup lang="ts">
import { Head } from '@inertiajs/vue3';
import { Box, Cable, House, Network, Sun, Zap } from '@lucide/vue';
import { ref } from 'vue';
import NetworkPlan3D from '@/components/NetworkPlan3D.vue';
import NetworkGraph from '@/components/NetworkGraph.vue';
import { panelGroups } from '@/components/network-plan/networkTopology';
import { networkPlan } from '@/routes';

const selected = ref('TR1');
const representation = ref<'3d' | 'graph'>('3d');
const supportVisible = ref(false);
const statistics = [
    {
        label: 'Distribution panels',
        value: '4',
        unit: 'T01–T04',
        icon: Network,
    },
    {
        label: 'Residential units',
        value: '30',
        unit: 'apartments',
        icon: House,
    },
    {
        label: 'Solar capacity',
        value: '60',
        unit: 'kW · 2 installations',
        icon: Sun,
    },
    {
        label: 'Shared transformer',
        value: '400',
        unit: 'kVA · 20 / 0.4 kV',
        icon: Zap,
    },
];

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
        <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <div
                v-for="stat in statistics"
                :key="stat.label"
                class="rounded-xl border border-sidebar-border/70 bg-card px-4 py-3.5 dark:border-sidebar-border"
            >
                <div class="flex items-center justify-between gap-2">
                    <p class="text-xs text-muted-foreground">
                        {{ stat.label }}
                    </p>
                    <component
                        :is="stat.icon"
                        class="size-3.5 text-muted-foreground"
                        aria-hidden="true"
                    />
                </div>
                <p class="mt-2 flex flex-wrap items-baseline gap-x-2">
                    <span class="text-2xl font-semibold tracking-tight">{{
                        stat.value
                    }}</span
                    ><span class="text-[11px] text-muted-foreground">{{
                        stat.unit
                    }}</span>
                </p>
            </div>
        </div>
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
                        representation === 'graph'
                            ? 'bg-background text-foreground shadow-xs'
                            : 'text-muted-foreground hover:text-foreground'
                    "
                    :aria-pressed="representation === 'graph'"
                    @click="representation = 'graph'"
                >
                    <Network class="size-3.5" aria-hidden="true" /> Graph view
                </button>
            </div>
        </div>
        <NetworkPlan3D
            v-if="representation === '3d'"
            v-model:selected="selected"
            v-model:support-visible="supportVisible"
        />
        <NetworkGraph
            v-else
            v-model:selected="selected"
            v-model:support-visible="supportVisible"
        />
        <section
            aria-label="Residential distribution"
            class="grid grid-cols-2 gap-3 xl:grid-cols-4"
        >
            <button
                v-for="panel in panelGroups"
                :key="panel.id"
                type="button"
                class="flex items-center justify-between gap-2 rounded-xl border bg-card px-4 py-3 text-left transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                :class="
                    selected === panel.id
                        ? 'border-amber-500/60'
                        : 'border-sidebar-border/70 dark:border-sidebar-border'
                "
                :aria-pressed="selected === panel.id"
                @click="selected = panel.id"
            >
                <div class="flex items-center gap-3">
                    <Cable
                        class="size-4 text-muted-foreground"
                        aria-hidden="true"
                    />
                    <div>
                        <h2 class="text-xs font-semibold">{{ panel.id }}</h2>
                        <p class="mt-0.5 text-[10px] text-muted-foreground">
                            {{ panel.bus }} · {{ panel.apartments }} apartments
                        </p>
                    </div>
                </div>
                <span class="text-lg font-medium tabular-nums">{{
                    panel.apartments
                }}</span>
            </button>
        </section>
        <p class="pb-1 text-[11px] leading-relaxed text-muted-foreground">
            Schematic layout based on the project topology. Positions and
            dwelling models are illustrative; equipment is not shown to scale.
        </p>
    </div>
</template>
