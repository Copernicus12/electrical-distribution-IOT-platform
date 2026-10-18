import { Group, MeshStandardMaterial, Vector3 } from 'three';
import { createDoorExterior } from './createDoorExterior';
import type { PanelMaterials, PanelModelTools } from './modelTypes';

/** Solid equipment door. +Z is the exterior; -Z carries the contact blocks and wiring. */
export function createControlDoor(
    parent: Group,
    tools: PanelModelTools,
    palette: PanelMaterials,
): Group {
    const { box, cable } = tools;
    const { metal, trim, back, terminal, duct, recess, wire } = palette;
    const door = new Group();
    door.name = 'left-control-door';
    door.position.set(-0.61, 1.49, 0.36);
    door.rotation.y = (-112 * Math.PI) / 180;
    parent.add(door);
    const width = 1.15;

    function accent(color: number): MeshStandardMaterial {
        const material = new MeshStandardMaterial({ color, roughness: 0.72 });
        tools.materials.add(material);
        return material;
    }
    const red = accent(0x853d3b);
    const blue = accent(0x3c5974);
    const yellow = accent(0x9b9050);
    const earth = accent(0x667e50);
    const marking = accent(0xa7a7a2);
    // Folded steel sheet, not an open ladder. Hardware exists on both faces.
    box(door, [width, 2.35, 0.035], [width / 2, 0, 0], metal);
    for (const x of [0.018, width - 0.018]) {
        box(door, [0.035, 2.35, 0.055], [x, 0, 0], trim);
    }
    for (const y of [-1.155, 1.155]) {
        box(door, [width, 0.035, 0.055], [width / 2, y, 0], trim);
    }
    box(door, [1.025, 2.14, 0.012], [width / 2, 0, -0.024], back);

    const contacts = createDoorExterior(door, tools, palette);
    const selectors = contacts.filter((contact) => contact.kind === 'selector');
    const auxiliaryContacts = contacts.filter(
        (contact) => contact.kind !== 'selector',
    );

    // Interior: selector contacts and wiring only; the multipole sockets live on the fixed side wall.
    for (const y of [1.03, 0.08, -0.73, -1.06]) {
        box(door, [1.03, 0.075, 0.085], [0.575, y, -0.088], duct);
        for (let slot = 0; slot < 26; slot++) {
            box(
                door,
                [0.02, 0.04, 0.006],
                [0.09 + slot * 0.038, y, -0.134],
                recess,
            );
        }
    }
    for (const { x, y } of selectors) {
        box(door, [0.1, 0.14, 0.07], [x, y, -0.065], recess);
        box(door, [0.085, 0.055, 0.025], [x, y - 0.028, -0.11], terminal);
        const ductY = y > 0.16 ? 1.03 : y > -0.6 ? 0.08 : -1.06;
        const strands = 3;
        for (let strand = 0; strand < strands; strand++) {
            const dx = (strand - (strands - 1) / 2) * 0.015;
            const bendX = x + 0.04 + strand * 0.008;
            const color = [red, blue, yellow][strand];
            cable(
                door,
                [
                    [x + dx, y - 0.02, -0.128],
                    [bendX, y - 0.11, -0.18],
                    [bendX + 0.015, (y + ductY) / 2, -0.16],
                    [x + dx, ductY, -0.132],
                ],
                0.0035,
                color,
            );
            box(
                door,
                [0.016, 0.025, 0.009],
                [x + dx, y - 0.045, -0.134],
                marking,
            );
        }
        // Short protective-earth loop and a cable tie on the outgoing bundle.
        cable(
            door,
            [
                [x - 0.03, y + 0.035, -0.11],
                [x - 0.055, y + 0.1, -0.15],
                [x + 0.04, y + 0.1, -0.15],
                [x + 0.04, y + 0.035, -0.11],
            ],
            0.003,
            earth,
        );
        box(door, [0.055, 0.01, 0.012], [x + 0.04, y - 0.11, -0.18], marking);
    }
    // The annunciator and push buttons also have visible backs and cable connections.
    for (const { x, y } of auxiliaryContacts) {
        box(door, [0.08, 0.08, 0.065], [x, y, -0.07], recess);
        for (const dx of [-0.018, 0.018]) {
            cable(
                door,
                [
                    [x + dx, y, -0.108],
                    [x + dx, y - 0.1, -0.15],
                    [x + dx, -1.06, -0.132],
                ],
                0.004,
                wire,
            );
        }
    }
    // A flexible harness crosses the hinge back into the cabinet.
    door.updateMatrix();
    for (let strand = 0; strand < 4; strand++) {
        const target = new Vector3(
            0.07 + strand * 0.018,
            -0.9,
            -0.15,
        ).applyMatrix4(door.matrix);
        cable(
            parent,
            [
                [-0.49, 0.5, -0.13],
                [-0.66, 0.43, 0.17],
                [-0.76, 0.47, 0.36],
                [target.x, target.y, target.z],
            ],
            0.006,
            strand === 0 ? earth : wire,
        );
    }
    return door;
}
