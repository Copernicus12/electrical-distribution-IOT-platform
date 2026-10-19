export type AssetKind =
    | 'grid'
    | 'transformer'
    | 'solar'
    | 'bus'
    | 'panel'
    | 'home';
export type Position = [number, number, number];

export type NetworkAsset = {
    id: string;
    name: string;
    kind: AssetKind;
    position: Position;
    description: string;
    specifications: { label: string; value: string }[];
    panelId?: string;
};

export type NetworkConnection = {
    id: string;
    from: string;
    to: string;
    kind: 'supply' | 'solar' | 'residential' | 'support';
    normallyOpen: boolean;
};

export const assetKindLabels: Record<AssetKind, string> = {
    grid: 'Utility supply',
    transformer: 'Distribution transformer',
    solar: 'Solar generation',
    bus: 'Common supply node',
    panel: 'Distribution panel',
    home: 'Residential unit',
};

export const panelGroups = [
    { id: 'T01', apartments: 8, x: -9, bus: 'BUS-A' },
    { id: 'T02', apartments: 7, x: -3, bus: 'BUS-A' },
    { id: 'T03', apartments: 8, x: 3, bus: 'BUS-B' },
    { id: 'T04', apartments: 7, x: 9, bus: 'BUS-B' },
] as const;

const infrastructure: NetworkAsset[] = [
    {
        id: 'GRID',
        name: 'Utility grid',
        kind: 'grid',
        position: [0, 0, -11],
        description:
            'Equivalent medium-voltage source supplying the neighbourhood.',
        specifications: [
            { label: 'Nominal voltage', value: '20 kV' },
            { label: 'Feeds', value: 'TR1' },
        ],
    },
    {
        id: 'TR1',
        name: 'Main transformer',
        kind: 'transformer',
        position: [0, 0, -7],
        description:
            'One shared transformer supplies all four panels through two common low-voltage nodes.',
        specifications: [
            { label: 'Rated power', value: '400 kVA' },
            { label: 'Voltage ratio', value: '20 / 0.4 kV' },
            { label: 'Supplies', value: 'T01–T04' },
        ],
    },
    ...(['A', 'B'] as const).map((group, index): NetworkAsset => ({
        id: 'BUS-' + group,
        name: 'Common node ' + group,
        kind: 'bus',
        position: [index === 0 ? -6 : 6, 0, -3.5],
        description:
            'The transformer and one PV installation connect to this shared node.',
        specifications: [
            { label: 'Nominal voltage', value: '400 V' },
            {
                label: 'Panel group',
                value: index === 0 ? 'T01 / T02' : 'T03 / T04',
            },
            { label: 'Local generation', value: index === 0 ? 'PV1' : 'PV2' },
        ],
    })),
    ...([1, 2] as const).map((number): NetworkAsset => ({
        id: 'PV' + number,
        name: 'Solar installation ' + number,
        kind: 'solar',
        position: [number === 1 ? -9 : 9, 0, -7],
        description:
            'Local PV generation connects once to the common node of its panel group.',
        specifications: [
            { label: 'Installed capacity', value: '30 kW' },
            { label: 'Connection', value: number === 1 ? 'BUS-A' : 'BUS-B' },
            {
                label: 'Panel group',
                value: number === 1 ? 'T01 / T02' : 'T03 / T04',
            },
        ],
    })),
];

export const networkAssets: NetworkAsset[] = [...infrastructure];
export const networkConnections: NetworkConnection[] = [
    {
        id: 'grid-tr',
        from: 'GRID',
        to: 'TR1',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 'tr-a',
        from: 'TR1',
        to: 'BUS-A',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 'tr-b',
        from: 'TR1',
        to: 'BUS-B',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 'pv-a',
        from: 'PV1',
        to: 'BUS-A',
        kind: 'solar',
        normallyOpen: false,
    },
    {
        id: 'pv-b',
        from: 'PV2',
        to: 'BUS-B',
        kind: 'solar',
        normallyOpen: false,
    },
    {
        id: 'a-t01',
        from: 'BUS-A',
        to: 'T01',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 't01-t02',
        from: 'T01',
        to: 'T02',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 'b-t03',
        from: 'BUS-B',
        to: 'T03',
        kind: 'supply',
        normallyOpen: false,
    },
    {
        id: 't03-t04',
        from: 'T03',
        to: 'T04',
        kind: 'supply',
        normallyOpen: false,
    },
];

let apartmentNumber = 0;
for (const panel of panelGroups) {
    networkAssets.push({
        id: panel.id,
        name: 'Electrical panel ' + panel.id,
        kind: 'panel',
        position: [panel.x, 0, 0],
        description:
            'Distributes power to its residential circuits and hosts the electrical, connection and ambient sensors.',
        specifications: [
            { label: 'Residential units', value: String(panel.apartments) },
            { label: 'Supply group', value: panel.bus },
            { label: 'Power analyser', value: 'PowerLogic PM3255' },
            { label: 'Monitoring', value: 'Electrical / connection / ambient' },
        ],
    });
    for (let index = 0; index < panel.apartments; index++) {
        apartmentNumber++;
        const id = 'A' + String(apartmentNumber).padStart(2, '0');
        networkAssets.push({
            id,
            name: 'Apartment ' + id,
            kind: 'home',
            panelId: panel.id,
            position: [
                panel.x + (index % 2 === 0 ? -1.15 : 1.15),
                0,
                3.3 + Math.floor(index / 2) * 1.8,
            ],
            description:
                'A schematic dwelling representing one two-room apartment. Consumption will be supplied by the electrical simulation.',
            specifications: [
                { label: 'Distribution panel', value: panel.id },
                { label: 'Dwelling type', value: 'Two-room apartment' },
                { label: 'Reference energy', value: '150–250 kWh / month' },
                { label: 'Load categories', value: 'Essential / flexible' },
            ],
        });
        networkConnections.push({
            id: panel.id + '-' + id,
            from: panel.id,
            to: id,
            kind: 'residential',
            normallyOpen: false,
        });
    }
}

for (const from of ['T01', 'T02']) {
    for (const to of ['T03', 'T04']) {
        networkConnections.push({
            id: from + '-' + to,
            from,
            to,
            kind: 'support',
            normallyOpen: true,
        });
    }
}

export const assetById = new Map(
    networkAssets.map((asset) => [asset.id, asset]),
);
