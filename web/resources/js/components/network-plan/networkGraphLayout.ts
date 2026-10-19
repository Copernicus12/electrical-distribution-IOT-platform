import {
    networkAssets,
    networkConnections,
    panelGroups,
} from './networkTopology';
import type { NetworkAsset, NetworkConnection } from './networkTopology';

export type GraphNode = {
    asset: NetworkAsset;
    x: number;
    y: number;
    width: number;
    height: number;
    subtitle: string;
};

const panelX = [160, 430, 770, 1040];
export const graphSize = { width: 1200, height: 920 };
export const graphNodes: GraphNode[] = networkAssets.map((asset) => {
    let x = 600;
    let y = 70;
    let width = 142;
    let height = 64;
    let subtitle = asset.specifications[0].value;
    if (asset.kind === 'transformer') y = 185;
    if (asset.kind === 'solar') {
        x = asset.id === 'PV1' ? 110 : 1090;
        y = 270;
    }
    if (asset.kind === 'bus') {
        x = asset.id === 'BUS-A' ? 330 : 870;
        y = 330;
        width = 120;
        height = 52;
    }
    if (asset.kind === 'panel') {
        x = panelX[panelGroups.findIndex((panel) => panel.id === asset.id)];
        y = 450;
        width = 136;
        subtitle += ' apartments';
    }
    if (asset.kind === 'home') {
        const panelIndex = panelGroups.findIndex(
            (panel) => panel.id === asset.panelId,
        );
        const siblings = networkAssets.filter(
            (entry) => entry.panelId === asset.panelId,
        );
        const index = siblings.findIndex((entry) => entry.id === asset.id);
        x = panelX[panelIndex] + (index % 2 === 0 ? -58 : 58);
        y = 654 + Math.floor(index / 2) * 62;
        width = 94;
        height = 42;
        subtitle = '2 rooms';
    }
    return { asset, x, y, width, height, subtitle };
});

export const graphNodeById = new Map(
    graphNodes.map((node) => [node.asset.id, node]),
);

export function graphConnectionPath(connection: NetworkConnection): string {
    const from = graphNodeById.get(connection.from)!;
    const to = graphNodeById.get(connection.to)!;
    const bottom = from.y + from.height / 2;
    const top = to.y - to.height / 2;
    if (connection.normallyOpen) {
        const index = networkConnections
            .filter((entry) => entry.normallyOpen)
            .findIndex((entry) => entry.id === connection.id);
        const lane = 520 + index * 18;
        const fx = from.x + 48,
            tx = to.x - 48;
        return (
            'M ' +
            fx +
            ' ' +
            bottom +
            ' V ' +
            lane +
            ' H ' +
            tx +
            ' V ' +
            (to.y + to.height / 2)
        );
    }
    if (connection.kind === 'residential') {
        const end = to.x < from.x ? to.x + to.width / 2 : to.x - to.width / 2;
        return 'M ' + from.x + ' ' + bottom + ' V ' + to.y + ' H ' + end;
    }
    if (connection.kind === 'solar') {
        const direction = to.x > from.x ? 1 : -1;
        const start = from.x + (from.width / 2) * direction;
        const end = to.x - (to.width / 2) * direction;
        const middle = (start + end) / 2;
        return (
            'M ' +
            start +
            ' ' +
            from.y +
            ' H ' +
            middle +
            ' V ' +
            to.y +
            ' H ' +
            end
        );
    }
    if (from.asset.kind === 'panel' && to.asset.kind === 'panel') {
        return (
            'M ' +
            (from.x + from.width / 2) +
            ' ' +
            from.y +
            ' H ' +
            (to.x - to.width / 2)
        );
    }
    const middle = from.asset.kind === 'transformer' ? 255 : (bottom + top) / 2;
    return (
        'M ' +
        from.x +
        ' ' +
        bottom +
        ' V ' +
        middle +
        ' H ' +
        to.x +
        ' V ' +
        top
    );
}
