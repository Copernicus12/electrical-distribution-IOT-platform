"""Balanced pandapower model for the four-panel neighborhood."""

import math

from ..connections.protocol import PANELS


class DistributionNetwork:
    def __init__(self):
        try:
            import pandapower as pp
        except ImportError as exc:
            raise RuntimeError("Install Python dependencies with: pip install -r requirements.txt") from exc

        self.pp = pp
        self.net = pp.create_empty_network(sn_mva=0.4, f_hz=50)
        hv = pp.create_bus(self.net, vn_kv=20, name="Grid 20 kV")
        lv = pp.create_bus(self.net, vn_kv=0.4, name="Transformer 0.4 kV")
        group_a = pp.create_bus(self.net, vn_kv=0.4, name="T01-T02 common node")
        group_b = pp.create_bus(self.net, vn_kv=0.4, name="T03-T04 common node")
        self.panel_buses = {
            "T01": pp.create_bus(self.net, vn_kv=0.4, name="T01"),
            "T02": pp.create_bus(self.net, vn_kv=0.4, name="T02"),
            "T03": pp.create_bus(self.net, vn_kv=0.4, name="T03"),
            "T04": pp.create_bus(self.net, vn_kv=0.4, name="T04"),
        }
        pp.create_ext_grid(self.net, bus=hv, vm_pu=1.0, name="20 kV source")
        self.trafo = pp.create_transformer_from_parameters(
            self.net, hv_bus=hv, lv_bus=lv, sn_mva=0.4, vn_hv_kv=20, vn_lv_kv=0.4,
            vk_percent=6.0, vkr_percent=1.0, pfe_kw=0.8, i0_percent=0.2,
            shift_degree=150, name="20/0.4 kV 400 kVA",
        )

        self._line(lv, group_a, "main-A", 0.12, 0.20)
        self._line(lv, group_b, "main-B", 0.12, 0.20)
        panel_edges = {
            "T01": (group_a, 0.05),
            "T02": (self.panel_buses["T01"], 0.05),
            "T03": (group_b, 0.05),
            "T04": (self.panel_buses["T03"], 0.05),
        }
        self.panel_lines = {}
        for panel, (parent, length_km) in panel_edges.items():
            self.panel_lines[panel] = self._line(
                parent, self.panel_buses[panel], panel, length_km, 0.05
            )

        self.tie_lines = {}
        for index, first in enumerate(PANELS):
            for second in PANELS[index + 1:]:
                line = self._line(
                    self.panel_buses[first], self.panel_buses[second],
                    "tie-{}-{}".format(first, second), 0.08, 0.05,
                )
                switch = pp.create_switch(
                    self.net, bus=self.panel_buses[first], element=line,
                    et="l", closed=False, type="LBS",
                    name="normally-open-{}-{}".format(first, second),
                )
                self.tie_lines[(first, second)] = {"line": line, "switch": switch}

        self.panel_loads = {
            panel: pp.create_load(self.net, bus=self.panel_buses[panel], p_mw=0, q_mvar=0,
                                  name="{} aggregated homes".format(panel))
            for panel in PANELS
        }
        self.panel_breaker_closed = {panel: True for panel in PANELS}
        self.pv_groups = {
            "PV1": pp.create_sgen(self.net, bus=group_a, p_mw=0, q_mvar=0,
                                   name="PV1 30 kW T01-T02"),
            "PV2": pp.create_sgen(self.net, bus=group_b, p_mw=0, q_mvar=0,
                                   name="PV2 30 kW T03-T04"),
        }
        self.last_results = None
        self.automatic_ties = {}
        self.last_panel_load_kw = {panel: 0.0 for panel in PANELS}
        self.last_pv_kw = {"PV1": 0.0, "PV2": 0.0}

    def _line(self, from_bus, to_bus, name, length_km, max_i_ka):
        return self.pp.create_line_from_parameters(
            self.net, from_bus=from_bus, to_bus=to_bus, length_km=length_km,
            r_ohm_per_km=0.32, x_ohm_per_km=0.08, c_nf_per_km=210,
            max_i_ka=max_i_ka, max_loading_percent=100, name=name,
        )

    def solve(self, panel_load_kw, pv_kw):
        self.last_panel_load_kw = dict(panel_load_kw)
        self.last_pv_kw = dict(pv_kw)
        for panel, load_kw in panel_load_kw.items():
            served_kw = max(0.0, load_kw) if self.panel_breaker_closed[panel] else 0.0
            power_mw = served_kw / 1000
            self.net.load.at[self.panel_loads[panel], "p_mw"] = power_mw
            self.net.load.at[self.panel_loads[panel], "q_mvar"] = power_mw * math.tan(math.acos(0.95))
        for group, power_kw in pv_kw.items():
            self.net.sgen.at[self.pv_groups[group], "p_mw"] = max(0.0, power_kw) / 1000

        self.pp.runpp(self.net, algorithm="nr", init="results", trafo_loading="current")
        self.last_results = {
            "panels": {},
            "transformer_loading_pct": float(self.net.res_trafo.at[self.trafo, "loading_percent"]),
            "grid_import_kw": float(self.net.res_ext_grid["p_mw"].sum() * 1000),
            "voltages_pu": {
                panel: float(self.net.res_bus.at[bus, "vm_pu"])
                for panel, bus in self.panel_buses.items()
            },
        }
        for panel, line in self.panel_lines.items():
            loading = float(self.net.res_line.at[line, "loading_percent"])
            voltage_pu = self.last_results["voltages_pu"][panel]
            load_kw = float(panel_load_kw[panel]) if self.panel_breaker_closed[panel] else 0.0
            line_result = self.net.res_line.loc[line]
            current_a = max(abs(float(line_result["i_from_ka"])), abs(float(line_result["i_to_ka"]))) * 1000
            self.last_results["panels"][panel] = {
                "load_kw": load_kw,
                "current_a": current_a,
                "line_loading_pct": loading,
                "voltage_pu": voltage_pu,
                "voltage_v": voltage_pu * 400 / math.sqrt(3),
            }
        self.last_results["line_loading_pct"] = {
            str(self.net.line.at[index, "name"]): float(self.net.res_line.at[index, "loading_percent"])
            for index in self.net.line.index
        }
        return self.last_results

    def set_breaker(self, panel, closed):
        self.panel_breaker_closed[panel] = bool(closed)

    def try_close_support(self, target_panel, donor_panel=None):
        """Close the safest normally-open tie that relieves target-panel current."""
        if self.last_results is None:
            return None
        before = self.last_results["panels"][target_panel]["line_loading_pct"]
        best = None
        for pair, link in self.tie_lines.items():
            if target_panel not in pair or bool(self.net.switch.at[link["switch"], "closed"]):
                continue
            if donor_panel is not None and donor_panel not in pair:
                continue
            self.net.switch.at[link["switch"], "closed"] = True
            try:
                self.pp.runpp(self.net, algorithm="nr", init="results", trafo_loading="current")
                target_line = self.panel_lines[target_panel]
                after = float(self.net.res_line.at[target_line, "loading_percent"])
                safe = self._within_limits()
                relief = before - after
                if safe and relief > 0.1 and (best is None or relief > best[0]):
                    best = (relief, pair, link["switch"])
            except Exception:
                pass
            self.net.switch.at[link["switch"], "closed"] = False

        if best is None:
            self.solve(self.last_panel_load_kw, self.last_pv_kw)
            return None

        _, pair, switch = best
        self.net.switch.at[switch, "closed"] = True
        self.automatic_ties[target_panel] = (pair, switch)
        self.solve(self.last_panel_load_kw, self.last_pv_kw)
        return pair

    def open_support(self, target_panel):
        link = self.automatic_ties.pop(target_panel, None)
        if link is None:
            return False
        self.net.switch.at[link[1], "closed"] = False
        self.solve(self.last_panel_load_kw, self.last_pv_kw)
        return True

    def is_feasible(self):
        return self._within_limits()

    def _within_limits(self):
        if not self.net.converged:
            return False
        if self.net.res_line["loading_percent"].max() > 100:
            return False
        if self.net.res_trafo["loading_percent"].max() > 100:
            return False
        voltages = self.net.res_bus["vm_pu"]
        return bool((voltages >= 0.95).all() and (voltages <= 1.05).all())
