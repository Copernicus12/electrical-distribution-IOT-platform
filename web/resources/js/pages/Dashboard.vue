<script setup lang="ts">
import { Head } from '@inertiajs/vue3';
import { ref } from 'vue';
import ElectricalPanel3DSchematic from '@/components/ElectricalPanel3DSchematic.vue';
import PlaceholderPattern from '@/components/PlaceholderPattern.vue';
import { dashboard } from '@/routes';

const panels = ref(
    ['T01', 'T02', 'T03', 'T04'].map((id) => ({ id, running: false })),
);

defineOptions({
    layout: {
        breadcrumbs: [
            {
                title: 'Dashboard',
                href: dashboard(),
            },
        ],
    },
});
</script>

<template>
    <Head title="Dashboard" />

    <div
        class="flex h-full flex-1 flex-col gap-4 overflow-x-auto rounded-xl p-4"
    >
        <div class="grid min-w-[880px] auto-rows-min grid-cols-4 gap-4">
            <ElectricalPanel3DSchematic
                v-for="panel in panels"
                :key="panel.id"
                v-model:running="panel.running"
                :panel-id="panel.id"
            />
        </div>
        <div
            class="relative min-h-[100vh] flex-1 rounded-xl border border-sidebar-border/70 md:min-h-min dark:border-sidebar-border"
        >
            <PlaceholderPattern />
        </div>
    </div>
</template>
