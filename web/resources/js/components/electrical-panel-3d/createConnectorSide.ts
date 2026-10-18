import { CylinderGeometry, Group, Mesh } from 'three';
import type { Material } from 'three';
import type { PanelMaterials, PanelModelTools } from './modelTypes';

/** Fixed multipole connector plate on the outside of the cabinet's left wall. */
export function createConnectorSide(
    cabinet: Group,
    tools: PanelModelTools,
    palette: PanelMaterials,
): Group {
    const { box, cable } = tools;
    const { metal, trim, back, terminal, recess, wire, duct } = palette;
    const side = new Group();
    side.name = 'fixed-left-connector-plate';
    side.position.set(-0.626, 1.48, 0);
    side.rotation.y = -Math.PI / 2;
    cabinet.add(side);

    // Local X follows cabinet depth; positive local Z points out of the left wall.
    box(side, [0.57, 2.17, 0.018], [0, -0.015, 0.013], back);
    const pinGeometry = new CylinderGeometry(0.5, 0.5, 1, 8);
    tools.geometries.add(pinGeometry);

    function pin(
        x: number,
        y: number,
        z: number,
        radius: number,
        material: Material,
    ): void {
        const mesh = new Mesh(pinGeometry, material);
        mesh.rotation.x = Math.PI / 2;
        mesh.scale.set(radius * 2, 0.005, radius * 2);
        mesh.position.set(x, y, z);
        side.add(mesh);
    }

    for (const x of [-0.264, 0.264]) {
        for (const y of [-1.065, -0.55, 0, 0.55, 1.035]) {
            pin(x, y, 0.026, 0.009, trim);
            box(side, [0.01, 0.002, 0.002], [x, y, 0.03], recess);
        }
    }

    function contactBack(x: number, y: number): void {
        // Rear contacts project into the fixed enclosure, with no wires on the door.
        box(side, [0.055, 0.065, 0.045], [x, y, -0.063], recess);
        box(side, [0.04, 0.035, 0.014], [x, y - 0.012, -0.092], terminal);
        for (const offset of [-0.012, 0, 0.012]) {
            cable(
                side,
                [
                    [x + offset, y - 0.012, -0.102],
                    [x + offset, y - 0.06, -0.135],
                    [-0.24, y - 0.08, -0.135],
                    [-0.265, y - 0.09, -0.105],
                ],
                0.0025,
                wire,
            );
        }
    }

    // Three dense rows of small connectors and blanking plates, as in the reference.
    for (let row = 0; row < 3; row++) {
        const y = 0.93 - row * 0.16;
        for (let column = 0; column < 7; column++) {
            const x = -0.234 + column * 0.078;
            box(side, [0.069, 0.1, 0.014], [x, y, 0.03], trim);
            if (column < (row === 0 ? 2 : 1)) {
                pin(x, y + 0.031, 0.041, 0.004, recess);
                pin(x, y - 0.031, 0.041, 0.004, recess);
                continue;
            }
            box(side, [0.051, 0.068, 0.035], [x, y, 0.055], recess);
            box(side, [0.035, 0.047, 0.012], [x, y, 0.078], terminal);
            for (const dx of [-0.009, 0.009]) {
                for (const dy of [-0.014, 0, 0.014])
                    pin(x + dx, y + dy, 0.087, 0.0035, recess);
            }
            box(side, [0.048, 0.01, 0.023], [x, y - 0.045, 0.055], trim);
            contactBack(x, y);
        }
    }

    // Larger rectangular industrial sockets with locking lugs and pin inserts.
    const occupiedColumns = [
        [0, 1, 2, 3],
        [0, 1, 2],
        [0, 1, 2, 3],
        [2, 3],
        [2, 3],
        [1, 2, 3],
    ];
    for (const [row, columns] of occupiedColumns.entries()) {
        const y = 0.37 - row * 0.27;
        for (let column = 0; column < 4; column++) {
            const x = -0.2055 + column * 0.137;
            box(side, [0.117, 0.205, 0.014], [x, y, 0.03], trim);
            if (!columns.includes(column)) {
                pin(x, y - 0.074, 0.042, 0.005, recess);
                pin(x, y + 0.074, 0.042, 0.005, recess);
                continue;
            }
            box(side, [0.101, 0.177, 0.06], [x, y, 0.067], recess);
            box(side, [0.066, 0.141, 0.014], [x, y, 0.104], terminal);
            for (const dx of [-0.017, 0, 0.017]) {
                for (let index = 0; index < 7; index++) {
                    pin(
                        x + dx,
                        y - 0.052 + index * 0.0175,
                        0.114,
                        0.0035,
                        recess,
                    );
                }
            }
            box(side, [0.014, 0.105, 0.025], [x - 0.056, y, 0.082], metal);
            box(side, [0.014, 0.105, 0.025], [x + 0.056, y, 0.082], metal);
            box(side, [0.094, 0.014, 0.021], [x, y + 0.086, 0.084], trim);
            box(side, [0.094, 0.014, 0.021], [x, y - 0.086, 0.084], trim);
            contactBack(x, y);
        }
    }

    box(side, [0.04, 2.11, 0.045], [-0.28, -0.01, -0.098], duct);
    return side;
}
