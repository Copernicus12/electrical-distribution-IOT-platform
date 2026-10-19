import { networkAssets } from './networkTopology';
import type { NetworkAsset, NetworkConnection } from './networkTopology';

export type MapPoint = { x: number; y: number };
export type MapAsset = MapPoint & {
    asset: NetworkAsset;
    district: string;
    location: string;
};
export type MapRoad = { id: string; name: string; path: string; width: number };
export const mapSize = { width: 1600, height: 1040 };
export const mapBounds = { x: 0, y: 0, ...mapSize };

export function smoothPath(points: MapPoint[]): string {
    if (!points.length) return '';
    let result = 'M ' + points[0].x + ' ' + points[0].y;
    for (let index = 0; index < points.length - 1; index++) {
        const before = points[Math.max(0, index - 1)],
            start = points[index];
        const end = points[index + 1],
            after = points[Math.min(points.length - 1, index + 2)];
        result +=
            ' C ' +
            (start.x + (end.x - before.x) / 6) +
            ' ' +
            (start.y + (end.y - before.y) / 6) +
            ' ' +
            (end.x - (after.x - start.x) / 6) +
            ' ' +
            (end.y - (after.y - start.y) / 6) +
            ' ' +
            end.x +
            ' ' +
            end.y;
    }
    return result;
}
const points = (values: number[][]): MapPoint[] =>
    values.map(([x, y]) => ({ x, y }));
export const riverPoints = points([
    [1030, -180],
    [1010, 100],
    [1055, 260],
    [960, 430],
    [935, 590],
    [820, 750],
    [870, 920],
    [800, 1200],
]);
export const canalPoints = points([
    [-160, 610],
    [170, 640],
    [360, 590],
    [540, 650],
    [720, 600],
    [935, 590],
]);
export const riverPath = smoothPath(riverPoints);
export const canalPath = smoothPath(canalPoints);

export const districts = [
    {
        id: 'T01',
        name: 'Cedar Quarter',
        x: 390,
        y: 320,
        labelX: 420,
        labelY: 170,
        angle: -15,
        street: 'Cedar Lane',
        seed: 11,
    },
    {
        id: 'T02',
        name: 'Old Mill',
        x: 440,
        y: 785,
        labelX: 235,
        labelY: 895,
        angle: -23,
        street: 'Old Mill Road',
        seed: 29,
    },
    {
        id: 'T03',
        name: 'Riverside',
        x: 1250,
        y: 300,
        labelX: 1305,
        labelY: 150,
        angle: 18,
        street: 'Riverside Walk',
        seed: 43,
    },
    {
        id: 'T04',
        name: 'Garden District',
        x: 1240,
        y: 785,
        labelX: 1350,
        labelY: 930,
        angle: 11,
        street: 'Garden Avenue',
        seed: 71,
    },
] as const;

export const mainRoads: MapRoad[] = [
    {
        id: 'civic',
        name: 'Civic Avenue',
        path: smoothPath(
            points([
                [-100, 355],
                [190, 315],
                [440, 250],
                [690, 278],
                [865, 312],
                [1040, 300],
                [1260, 280],
                [1700, 375],
            ]),
        ),
        width: 13,
    },
    {
        id: 'west',
        name: 'West Embankment',
        path: smoothPath(
            points([
                [625, -100],
                [650, 170],
                [730, 355],
                [780, 525],
                [705, 730],
                [665, 930],
                [750, 1180],
            ]),
        ),
        width: 12,
    },
    {
        id: 'mill',
        name: 'Old Mill Road',
        path: smoothPath(
            points([
                [-100, 880],
                [180, 810],
                [340, 755],
                [545, 810],
                [730, 865],
                [940, 845],
                [1210, 760],
                [1690, 840],
            ]),
        ),
        width: 12,
    },
    {
        id: 'garden',
        name: 'Garden Avenue',
        path: smoothPath(
            points([
                [1420, -100],
                [1370, 210],
                [1450, 410],
                [1310, 600],
                [1335, 835],
                [1230, 1180],
            ]),
        ),
        width: 11,
    },
    {
        id: 'cedar',
        name: 'Cedar Lane',
        path: smoothPath(
            points([
                [-100, 125],
                [150, 180],
                [285, 330],
                [340, 490],
                [390, 610],
                [470, 760],
                [435, 1110],
            ]),
        ),
        width: 10,
    },
    {
        id: 'riverside',
        name: 'Riverside Walk',
        path: smoothPath(
            points([
                [1160, -120],
                [1140, 180],
                [1220, 390],
                [1130, 580],
                [1050, 730],
                [1105, 1060],
            ]),
        ),
        width: 9,
    },
];

function random(seed: number): () => number {
    let value = seed >>> 0;
    return () => {
        value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
        return value / 4294967296;
    };
}
function distanceToPath(point: MapPoint, line: MapPoint[]): number {
    let minimum = Infinity;
    for (let index = 1; index < line.length; index++) {
        const from = line[index - 1],
            to = line[index];
        const dx = to.x - from.x,
            dy = to.y - from.y;
        const t = Math.max(
            0,
            Math.min(
                1,
                ((point.x - from.x) * dx + (point.y - from.y) * dy) /
                    (dx * dx + dy * dy),
            ),
        );
        minimum = Math.min(
            minimum,
            Math.hypot(point.x - from.x - dx * t, point.y - from.y - dy * t),
        );
    }
    return minimum;
}
export function isWater(point: MapPoint): boolean {
    return (
        distanceToPath(point, riverPoints) < 76 ||
        distanceToPath(point, canalPoints) < 44
    );
}
/** Streets and buildings use the same continuous grid, with no overlapping district grids. */
export function streetGridPoint(column: number, row: number): MapPoint {
    const x = column * 52,
        y = row * 46;
    const wx = x + 24 * Math.sin(y / 210) + 16 * Math.sin((x + y) / 430);
    const wy = y + 23 * Math.sin(x / 260) + 12 * Math.sin(y / 300);
    const angle = (-9 * Math.PI) / 180;
    return {
        x: 800 + (wx - 800) * Math.cos(angle) - (wy - 520) * Math.sin(angle),
        y: 520 + (wx - 800) * Math.sin(angle) + (wy - 520) * Math.cos(angle),
    };
}
export function blockPoint(
    column: number,
    row: number,
    u: number,
    v: number,
): MapPoint {
    const a = streetGridPoint(column, row),
        b = streetGridPoint(column + 1, row);
    const c = streetGridPoint(column + 1, row + 1),
        d = streetGridPoint(column, row + 1);
    return {
        x:
            a.x * (1 - u) * (1 - v) +
            b.x * u * (1 - v) +
            c.x * u * v +
            d.x * (1 - u) * v,
        y:
            a.y * (1 - u) * (1 - v) +
            b.y * u * (1 - v) +
            c.y * u * v +
            d.y * (1 - u) * v,
    };
}
export const localRoads: string[] = [];
export const buildingFootprints: string[] = [];
export const buildingPlots: {
    column: number;
    row: number;
    u0: number;
    u1: number;
    v0: number;
    v1: number;
    corners: MapPoint[];
}[] = [];
const columns = Array.from({ length: 51 }, (_, index) => index - 10);
const rows = Array.from({ length: 41 }, (_, index) => index - 8);
for (const row of rows)
    localRoads.push(
        smoothPath(columns.map((column) => streetGridPoint(column, row))),
    );
for (const column of columns)
    localRoads.push(
        smoothPath(rows.map((row) => streetGridPoint(column, row))),
    );
const buildingRandom = random(7319);
for (const row of rows.slice(0, -1)) {
    for (const column of columns.slice(0, -1)) {
        for (let slot = 0; slot < 3; slot++) {
            if (buildingRandom() < 0.13) continue;
            const u0 = 0.15 + slot * 0.24 + buildingRandom() * 0.015;
            const u1 = u0 + 0.15 + buildingRandom() * 0.035;
            const v0 = 0.17 + buildingRandom() * 0.025;
            const v1 = 0.7 + buildingRandom() * 0.1;
            const corners = [
                [u0, v0],
                [u1, v0],
                [u1, v1],
                [u0, v1],
            ].map(([u, v]) => blockPoint(column, row, u, v));
            buildingPlots.push({ column, row, u0, u1, v0, v1, corners });
            buildingFootprints.push(
                'M ' +
                    corners
                        .map(
                            (point) =>
                                point.x.toFixed(2) + ' ' + point.y.toFixed(2),
                        )
                        .join(' L ') +
                    ' Z',
            );
        }
    }
}
const infrastructure: Record<
    string,
    MapPoint & { district: string; location: string }
> = {
    GRID: {
        x: 150,
        y: 155,
        district: 'Cedar Quarter',
        location: 'Utility intake · West service road',
    },
    TR1: {
        x: 665,
        y: 205,
        district: 'Utility precinct',
        location: 'Main substation · Civic Avenue',
    },
    'BUS-A': {
        x: 585,
        y: 427,
        district: 'Cedar Quarter',
        location: 'West common node · Cedar Lane',
    },
    'BUS-B': {
        x: 1185,
        y: 505,
        district: 'Riverside',
        location: 'East common node · Riverside Walk',
    },
    PV1: {
        x: 180,
        y: 450,
        district: 'Cedar Quarter',
        location: 'West solar field · Cedar Lane',
    },
    PV2: {
        x: 1440,
        y: 545,
        district: 'Garden District',
        location: 'East solar field · Garden Avenue',
    },
};
export const mapAssets: MapAsset[] = [];
for (const asset of networkAssets.filter((entry) => entry.kind !== 'home')) {
    const district = districts.find((entry) => entry.id === asset.id);
    const location = infrastructure[asset.id] ?? {
        x: district!.x,
        y: district!.y,
        district: district!.name,
        location: district!.street + ' · distribution junction',
    };
    mapAssets.push({ asset, ...location });
}
for (const district of districts) {
    const rng = random(district.seed * 73);
    const homes = networkAssets.filter(
        (asset) => asset.panelId === district.id,
    );
    for (const [index, asset] of homes.entries()) {
        let point: MapPoint = { x: district.x, y: district.y };
        let placed = false;
        for (let attempt = 0; attempt < 500; attempt++) {
            const angle = rng() * Math.PI * 2,
                radius = 85 + rng() * 170;
            point = {
                x: district.x + Math.cos(angle) * radius,
                y: district.y + Math.sin(angle) * radius * 0.73,
            };
            if (
                point.x > 65 &&
                point.x < 1535 &&
                point.y > 110 &&
                point.y < 970 &&
                !isWater(point) &&
                mapAssets.every(
                    (entry) =>
                        Math.hypot(entry.x - point.x, entry.y - point.y) > 46,
                )
            ) {
                placed = true;
                break;
            }
        }
        if (!placed)
            throw new Error('Unable to place residential asset ' + asset.id);
        mapAssets.push({
            asset,
            ...point,
            district: district.name,
            location:
                district.street + ' ' + (index * 2 + 3) + ' · ' + district.name,
        });
    }
}
export const mapAssetById = new Map(
    mapAssets.map((entry) => [entry.asset.id, entry]),
);

/** Curved routes avoid the rigid hierarchy of the logical diagram. */
export function mapConnectionPath(connection: NetworkConnection): string {
    const from = mapAssetById.get(connection.from)!,
        to = mapAssetById.get(connection.to)!;
    const dx = to.x - from.x,
        dy = to.y - from.y;
    const bend = connection.normallyOpen
        ? -0.24
        : connection.kind === 'residential'
          ? 0.12
          : 0.2;
    return (
        'M ' +
        from.x +
        ' ' +
        from.y +
        ' Q ' +
        ((from.x + to.x) / 2 - dy * bend) +
        ' ' +
        ((from.y + to.y) / 2 + dx * bend) +
        ' ' +
        to.x +
        ' ' +
        to.y
    );
}
