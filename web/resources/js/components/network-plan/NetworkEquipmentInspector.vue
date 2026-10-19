<script setup lang="ts">
import { Focus, Layers, MousePointer2 } from '@lucide/vue';
import { computed, useId } from 'vue';
import {
    assetById,
    assetKindLabels,
    networkAssets,
    networkConnections,
} from '@/components/network-plan/networkTopology';
import type { AssetKind } from '@/components/network-plan/networkTopology';
import { Button } from '@/components/ui/button';

defineProps<{ focusDisabled?: boolean }>();
const emit = defineEmits<{ focus: [id: string] }>();
const selectedId = defineModel<string>('selected', { default: 'TR1' });
const selected = computed(
    () => assetById.get(selectedId.value) ?? assetById.get('TR1')!,
);
const connections = computed(() =>
    networkConnections.filter(
        (connection) =>
            connection.from === selected.value.id ||
            connection.to === selected.value.id,
    ),
);
const assetGroups = (Object.keys(assetKindLabels) as AssetKind[]).map(
    (kind) => ({
        kind,
        label: assetKindLabels[kind],
        assets: networkAssets.filter((asset) => asset.kind === kind),
    }),
);
const id = useId();
function select(id: string): void {
    selectedId.value = id;
}
</script>

<template>
    <aside
        class="flex min-w-0 flex-col border-t border-border lg:border-t-0 lg:border-l"
        aria-label="Equipment details"
    >
        <div class="border-b border-border p-4">
            <label
                :for="id + '-asset'"
                class="mb-2 flex items-center gap-2 text-xs font-medium"
                ><MousePointer2
                    class="size-3.5 text-muted-foreground"
                    aria-hidden="true"
                />
                Inspect equipment</label
            >
            <select
                :id="id + '-asset'"
                v-model="selectedId"
                class="h-9 w-full min-w-0 rounded-md border border-input bg-background px-2 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
                <optgroup
                    v-for="group in assetGroups"
                    :key="group.kind"
                    :label="group.label"
                >
                    <option
                        v-for="asset in group.assets"
                        :key="asset.id"
                        :value="asset.id"
                    >
                        {{ asset.id }} · {{ asset.name }}
                    </option>
                </optgroup>
            </select>
        </div>
        <div class="flex-1 p-4" aria-live="polite" aria-atomic="true">
            <p
                class="text-[10px] font-medium tracking-widest text-muted-foreground uppercase"
            >
                {{ assetKindLabels[selected.kind] }}
            </p>
            <h2 class="mt-1 text-xl font-semibold tracking-tight">
                {{ selected.id }}
            </h2>
            <p class="mt-2 text-xs leading-relaxed text-muted-foreground">
                {{ selected.description }}
            </p>
            <dl class="mt-5 space-y-3">
                <div
                    v-for="spec in selected.specifications"
                    :key="spec.label"
                    class="flex flex-col gap-0.5"
                >
                    <dt class="text-[10px] text-muted-foreground">
                        {{ spec.label }}
                    </dt>
                    <dd class="text-xs font-medium">
                        {{ spec.value }}
                    </dd>
                </div>
            </dl>
            <Button
                variant="outline"
                size="sm"
                class="mt-5 w-full text-xs"
                :disabled="focusDisabled"
                @click="emit('focus', selected.id)"
                ><Focus class="size-3.5" aria-hidden="true" /> Focus
                equipment</Button
            >
            <div class="mt-5 border-t border-border pt-4">
                <h3
                    class="mb-2 text-[10px] font-medium tracking-widest text-muted-foreground uppercase"
                >
                    Connections
                </h3>
                <div class="flex flex-wrap gap-1.5">
                    <button
                        v-for="connection in connections"
                        :key="connection.id"
                        type="button"
                        class="rounded border border-border px-2 py-1 text-[10px] hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                        :title="
                            connection.normallyOpen
                                ? 'Normally open support link'
                                : 'Design connection'
                        "
                        @click="
                            select(
                                connection.from === selected.id
                                    ? connection.to
                                    : connection.from,
                            )
                        "
                    >
                        {{
                            connection.from === selected.id
                                ? connection.to
                                : connection.from
                        }}<span
                            v-if="connection.normallyOpen"
                            class="ml-1 text-muted-foreground"
                            >· open</span
                        >
                    </button>
                </div>
            </div>
        </div>
        <p
            class="flex items-start gap-2 border-t border-border px-4 py-3 text-[10px] leading-relaxed text-muted-foreground"
        >
            <Layers class="mt-0.5 size-3 shrink-0" aria-hidden="true" />
            Layout and equipment ratings only. Live power flows are not
            connected.
        </p>
    </aside>
</template>
