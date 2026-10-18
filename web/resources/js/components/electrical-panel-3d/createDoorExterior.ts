import {
    CanvasTexture,
    CylinderGeometry,
    Group,
    Mesh,
    MeshBasicMaterial,
    MeshStandardMaterial,
    PlaneGeometry,
    SRGBColorSpace,
    TorusGeometry,
} from 'three';
import type { Material, Vector3Tuple } from 'three';
import type { PanelMaterials, PanelModelTools } from './modelTypes';

export type DoorContact = {
    x: number;
    y: number;
    kind: 'selector' | 'auxiliary' | 'breaker';
};

/** Screen printing is procedural; selectors, counters, handles and breakers are solid geometry. */
export function createDoorExterior(
    door: Group,
    tools: PanelModelTools,
    palette: PanelMaterials,
): DoorContact[] {
    const { box } = tools;
    const { metal, trim, terminal, recess } = palette;
    const exterior = new Group();
    exterior.name = 'door-exterior';
    door.add(exterior);
    const contacts: DoorContact[] = [];
    const x = (u: number) => 0.08 + u * 0.99;
    const y = (v: number) => 1.1 - v * 2.2;

    function material(color: number, roughness = 0.7): MeshStandardMaterial {
        const value = new MeshStandardMaterial({
            color,
            roughness,
            metalness: 0.12,
        });
        tools.materials.add(value);
        return value;
    }
    const plastic = material(0xb4b7b1);
    const red = material(0x9e3029);
    const yellow = material(0xb4a337);
    const blue = material(0x315e80);
    const cylinder = new CylinderGeometry(0.5, 0.5, 1, 16);
    const plane = new PlaneGeometry(1, 1);
    const padlockLoop = new TorusGeometry(0.009, 0.0025, 5, 10);
    tools.geometries.add(cylinder);
    tools.geometries.add(plane);
    tools.geometries.add(padlockLoop);

    function roundPart(
        parent: Group,
        position: Vector3Tuple,
        radius: number,
        depth: number,
        surface: Material,
    ): Mesh {
        const mesh = new Mesh(cylinder, surface);
        mesh.rotation.x = Math.PI / 2;
        mesh.scale.set(radius * 2, depth, radius * 2);
        mesh.position.set(...position);
        parent.add(mesh);
        return mesh;
    }

    function texture(
        width: number,
        height: number,
        paint: (context: CanvasRenderingContext2D) => void,
    ): CanvasTexture {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext('2d');
        if (context) paint(context);
        const value = new CanvasTexture(canvas);
        value.colorSpace = SRGBColorSpace;
        value.anisotropy = 2;
        tools.textures.add(value);
        return value;
    }

    function decalMaterial(map: CanvasTexture): MeshBasicMaterial {
        const value = new MeshBasicMaterial({
            map,
            transparent: true,
            depthWrite: false,
        });
        tools.materials.add(value);
        return value;
    }

    function decal(
        parent: Group,
        width: number,
        height: number,
        position: Vector3Tuple,
        surface: Material,
    ): void {
        const mesh = new Mesh(plane, surface);
        mesh.scale.set(width, height, 1);
        mesh.position.set(...position);
        parent.add(mesh);
    }

    // Separate bolted cover panels preserve the proportions and blank upper area of the reference.
    box(exterior, [0.99, 0.12, 0.015], [0.575, y(0.028), 0.027], trim);
    box(exterior, [0.99, 0.31, 0.014], [0.575, y(0.129), 0.027], metal);
    box(exterior, [0.99, 1.14, 0.014], [0.575, y(0.452), 0.027], terminal);
    for (const u of [0.015, 0.985]) {
        for (const v of [
            0.015, 0.065, 0.2, 0.27, 0.61, 0.71, 0.79, 0.88, 0.97,
        ]) {
            roundPart(exterior, [x(u), y(v), 0.039], 0.009, 0.008, trim);
            box(exterior, [0.009, 0.002, 0.002], [x(u), y(v), 0.044], recess);
        }
    }

    const print = texture(768, 1792, (context) => {
        const w = 768,
            h = 1792;
        context.strokeStyle = '#1a1d1e';
        context.fillStyle = '#1a1d1e';
        context.lineJoin = 'miter';
        const text = (
            label: string,
            u: number,
            v: number,
            size = 12,
            align: CanvasTextAlign = 'left',
        ) => {
            context.font = `${size}px Arial, sans-serif`;
            context.textAlign = align;
            context.fillText(label, u * w, v * h);
        };
        const path = (points: [number, number][], weight: number) => {
            context.lineWidth = weight;
            context.beginPath();
            points.forEach(([u, v], index) =>
                index
                    ? context.lineTo(u * w, v * h)
                    : context.moveTo(u * w, v * h),
            );
            context.stroke();
        };
        text('STRATTON 1', 0.5, 0.045, 42, 'center');
        text('RESERVE BUSBAR 1', 0.95, 0.204, 16, 'right');
        text('MAIN BUSBAR 1', 0.95, 0.247, 16, 'right');
        path(
            [
                [0.045, 0.218],
                [0.95, 0.218],
            ],
            7,
        );
        path(
            [
                [0.045, 0.255],
                [0.95, 0.255],
            ],
            7,
        );
        path(
            [
                [0.045, 0.23],
                [0.95, 0.23],
            ],
            1.5,
        );
        path(
            [
                [0.3, 0.218],
                [0.3, 0.387],
                [0.61, 0.387],
                [0.61, 0.255],
            ],
            4,
        );
        path(
            [
                [0.045, 0.285],
                [0.235, 0.285],
                [0.235, 0.324],
                [0.3, 0.324],
            ],
            2,
        );
        path(
            [
                [0.045, 0.31],
                [0.16, 0.31],
                [0.16, 0.39],
                [0.37, 0.39],
                [0.37, 0.42],
            ],
            4,
        );
        path(
            [
                [0.045, 0.365],
                [0.3, 0.365],
            ],
            3,
        );
        path(
            [
                [0.66, 0.255],
                [0.66, 0.305],
                [0.79, 0.305],
                [0.79, 0.375],
                [0.61, 0.375],
            ],
            4,
        );
        path(
            [
                [0.5, 0.387],
                [0.5, 0.61],
            ],
            4,
        );
        path(
            [
                [0.51, 0.392],
                [0.51, 0.61],
            ],
            1,
        );
        path(
            [
                [0.5, 0.492],
                [0.67, 0.492],
            ],
            3,
        );
        path(
            [
                [0.5, 0.541],
                [0.56, 0.541],
            ],
            3,
        );
        path(
            [
                [0.5, 0.592],
                [0.71, 0.592],
            ],
            3,
        );
        path(
            [
                [0.24, 0.567],
                [0.5, 0.567],
            ],
            2,
        );
        for (const [u, v] of [
            [0.37, 0.365],
            [0.72, 0.375],
            [0.57, 0.492],
            [0.49, 0.541],
            [0.58, 0.592],
        ]) {
            context.beginPath();
            context.arc(u * w, v * h, 9, 0, Math.PI * 2);
            context.stroke();
        }
        context.beginPath();
        context.moveTo(0.485 * w, 0.605 * h);
        context.lineTo(0.515 * w, 0.605 * h);
        context.lineTo(0.5 * w, 0.617 * h);
        context.closePath();
        context.fill();
        const labels = [
            ['A103 (Q3)', 0.25, 0.295],
            ['A104 (Q4)', 0.66, 0.277],
            ['A102 (Q2)', 0.16, 0.361],
            ['A104ED (QS1)', 0.79, 0.346],
            ['A105 (Q6)', 0.5, 0.417],
            ['A105ED (QS1)', 0.67, 0.463],
            ['A103 (Q9)', 0.56, 0.512],
            ['A101 (Q8)', 0.71, 0.563],
        ] as const;
        for (const [label, u, v] of labels) text(label, u, v, 10, 'center');
        for (const v of [0.402, 0.458, 0.511, 0.56]) {
            context.lineWidth = 0.8;
            context.strokeRect(0.39 * w, (v - 0.004) * h, 0.065 * w, 0.008 * h);
            text('105-Q1', 0.422, v + 0.002, 7, 'center');
        }
        text('ACKNOWLEDGE', 0.24, 0.497, 8, 'center');
        text('LAMP TEST', 0.24, 0.537, 8, 'center');
        context.fillStyle = '#70423a';
        text('CURRENT TRANSFORMER TEST TERMINALS', 0.5, 0.633, 8, 'center');
        context.fillStyle = '#1a1d1e';
        for (let group = 0; group < 4; group++) {
            text(`103-${group + 1}G`, 0.12 + group * 0.13, 0.648, 7, 'center');
        }
        for (const [v, label] of [
            [0.727, 'SWITCH DISCONNECTORS'],
            [0.815, 'AUXILIARY CIRCUITS'],
            [0.905, 'CONTROL CIRCUITS'],
        ] as const) {
            context.fillRect(0.035 * w, v * h, 0.88 * w, 0.009 * h);
            context.fillStyle = '#bcbdb7';
            text(label, 0.06, v + 0.0067, 7);
            context.fillStyle = '#1a1d1e';
        }
    });
    decal(exterior, 0.99, 2.2, [0.575, 0, 0.036], decalMaterial(print));

    // Counters sit beside, rather than in a repeated two-column grid with, the selectors.
    const counterFace = decalMaterial(
        texture(192, 112, (context) => {
            context.fillStyle = '#b2b4af';
            context.fillRect(0, 0, 192, 112);
            context.strokeStyle = '#666a68';
            context.strokeRect(1, 1, 190, 110);
            context.fillStyle = '#202424';
            context.textAlign = 'center';
            context.font = '12px Arial';
            context.fillText('OPERATION COUNTER', 96, 30);
            context.fillRect(28, 50, 136, 38);
            context.fillStyle = '#c4c9bc';
            context.font = '26px monospace';
            context.fillText('00000', 96, 78);
        }),
    );
    function counter(u: number, v: number): void {
        box(exterior, [0.12, 0.072, 0.026], [x(u), y(v), 0.051], plastic);
        decal(exterior, 0.108, 0.063, [x(u), y(v), 0.065], counterFace);
    }
    for (const [u, v] of [
        [0.115, 0.324],
        [0.845, 0.305],
        [0.2, 0.425],
        [0.68, 0.427],
        [0.84, 0.427],
        [0.84, 0.492],
        [0.75, 0.541],
        [0.88, 0.592],
    ])
        counter(u, v);

    const selectors = [
        [0.25, 0.324, 0],
        [0.66, 0.305, 0],
        [0.16, 0.39, -0.1],
        [0.79, 0.375, -0.05],
        [0.5, 0.446, -0.05],
        [0.67, 0.492, -0.08],
        [0.56, 0.541, -0.1],
        [0.71, 0.592, -0.08],
        [0.16, 0.576, 0.35],
    ];
    for (const [index, [u, v, angle]] of selectors.entries()) {
        const selector = new Group();
        selector.name = `rotary-selector-${index + 1}`;
        selector.position.set(x(u), y(v), 0);
        exterior.add(selector);
        box(selector, [0.112, 0.12, 0.018], [0, 0, 0.052], plastic);
        box(selector, [0.086, 0.075, 0.025], [0, -0.015, 0.07], recess);
        roundPart(selector, [0, 0, 0.092], 0.033, 0.04, recess);
        const grip = new Mesh(cylinder, recess);
        grip.rotation.z = -Math.PI / 2 + angle;
        grip.scale.set(0.034, 0.082, 0.034);
        grip.position.set(-0.017, -0.003, 0.125);
        selector.add(grip);
        box(selector, [0.062, 0.017, 0.02], [0, -0.053, 0.087], red);
        box(selector, [0.048, 0.011, 0.021], [0, -0.069, 0.075], red);
        contacts.push({ x: x(u), y: y(v), kind: 'selector' });
    }

    // White annunciator with a raised dark frame, then red acknowledge and black lamp-test buttons.
    const annunciatorFace = decalMaterial(
        texture(192, 320, (context) => {
            context.fillStyle = '#cbc9bc';
            context.fillRect(0, 0, 192, 320);
            context.fillStyle = '#242729';
            context.textAlign = 'center';
            context.font = '11px Arial';
            context.fillText('ANNUNCIATOR', 92, 18);
            for (let row = 0; row < 12; row++) {
                const py = 37 + row * 22;
                context.fillStyle = '#515954';
                context.beginPath();
                context.arc(16, py, 3, 0, Math.PI * 2);
                context.fill();
                context.fillStyle = '#373d3a';
                context.font = '9px Arial';
                context.textAlign = 'left';
                context.fillText(`ALARM ${row + 1}`, 29, py + 3);
                context.strokeStyle = '#8a8d82';
                context.strokeRect(25, py - 7, 104, 16);
            }
            context.strokeStyle = '#4a4d48';
            context.strokeRect(143, 29, 35, 270);
            context.font = '15px Arial';
            context.fillStyle = '#242729';
            context.fillText('R', 154, 67);
            context.fillText('T', 154, 286);
        }),
    );
    box(exterior, [0.17, 0.245, 0.027], [x(0.16), y(0.46), 0.055], recess);
    decal(exterior, 0.15, 0.224, [x(0.16), y(0.46), 0.07], annunciatorFace);
    contacts.push({ x: x(0.16), y: y(0.46), kind: 'auxiliary' });
    for (const [v, surface] of [
        [0.519, red],
        [0.554, recess],
    ] as const) {
        roundPart(exterior, [x(0.24), y(v), 0.058], 0.035, 0.028, trim);
        roundPart(exterior, [x(0.24), y(v), 0.085], 0.025, 0.03, surface);
        contacts.push({ x: x(0.24), y: y(v), kind: 'auxiliary' });
    }

    // Colour-coded test terminals and two columns of four winged test switches.
    for (let group = 0; group < 4; group++) {
        for (let row = 0; row < 3; row++) {
            for (const [offset, surface] of [
                [-0.015, yellow],
                [0.015, blue],
            ] as const) {
                roundPart(
                    exterior,
                    [
                        x(0.12 + group * 0.13) + offset,
                        y(0.66 + row * 0.016),
                        0.052,
                    ],
                    0.01,
                    0.018,
                    surface,
                );
                roundPart(
                    exterior,
                    [
                        x(0.12 + group * 0.13) + offset,
                        y(0.66 + row * 0.016),
                        0.063,
                    ],
                    0.004,
                    0.005,
                    recess,
                );
            }
        }
    }
    for (const u of [0.72, 0.84]) {
        for (let row = 0; row < 4; row++) {
            const py = y(0.662 + row * 0.015);
            roundPart(exterior, [x(u), py, 0.056], 0.014, 0.025, recess);
            box(exterior, [0.071, 0.015, 0.021], [x(u), py, 0.078], recess);
        }
    }

    // Long curved-effect door handle with red maker plates at its ends.
    for (const v of [0.58, 0.68])
        box(exterior, [0.052, 0.065, 0.012], [1.087, y(v), 0.045], red);
    box(exterior, [0.038, 0.25, 0.043], [1.087, y(0.63), 0.064], recess);
    roundPart(exterior, [1.087, y(0.62), 0.091], 0.023, 0.03, recess);
    const handle = new Mesh(cylinder, recess);
    handle.scale.set(0.032, 0.22, 0.032);
    handle.position.set(1.087, y(0.63), 0.1);
    exterior.add(handle);

    // Lower covers: four red/yellow isolators, a locked breaker row, then a plain breaker row.
    const rows = [
        { v: 0.765, count: 4, isolators: true, locked: false },
        { v: 0.853, count: 16, isolators: false, locked: true },
        { v: 0.943, count: 14, isolators: false, locked: false },
    ];
    for (const [rowIndex, row] of rows.entries()) {
        const py = y(row.v);
        const bank = new Group();
        bank.name = `lower-breaker-row-${rowIndex + 1}`;
        exterior.add(bank);
        box(bank, [0.96, 0.16, 0.018], [0.575, py, 0.043], plastic);
        box(bank, [0.83, 0.105, 0.013], [0.55, py, 0.057], recess);
        const start = x(0.06),
            step = row.isolators ? 0.17 : 0.76 / row.count;
        for (let index = 0; index < row.count; index++) {
            const px = start + step * (index + 0.5);
            const w = row.isolators ? 0.14 : step * 0.95;
            box(bank, [w, 0.106, 0.036], [px, py, 0.081], plastic);
            box(
                bank,
                [w * 0.94, 0.018, 0.007],
                [px, py + 0.044, 0.104],
                recess,
            );
            box(bank, [w * 0.9, 0.006, 0.005], [px, py + 0.027, 0.104], red);
            if (row.isolators) {
                box(
                    bank,
                    [0.075, 0.048, 0.022],
                    [px, py - 0.008, 0.11],
                    yellow,
                );
                box(bank, [0.087, 0.024, 0.025], [px, py - 0.018, 0.132], red);
                contacts.push({ x: px, y: py, kind: 'breaker' });
            } else {
                box(bank, [w * 0.65, 0.037, 0.018], [px, py, 0.109], recess);
                if (index % 4 === 0)
                    contacts.push({ x: px, y: py, kind: 'breaker' });
                if (row.locked && index % 2 === 0) {
                    box(
                        bank,
                        [0.025, 0.028, 0.016],
                        [px, py - 0.042, 0.129],
                        yellow,
                    );
                    const loop = new Mesh(padlockLoop, trim);
                    loop.position.set(px, py - 0.023, 0.13);
                    bank.add(loop);
                }
            }
        }
    }
    return contacts;
}
