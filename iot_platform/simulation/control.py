"""Local overload response for simulated panels."""

import uuid


class EdgeController:
    def __init__(self, start_ratio=0.8, restore_ratio=0.7, hold_s=10, restore_s=30):
        self.start_ratio = start_ratio
        self.restore_ratio = restore_ratio
        self.hold_s = hold_s
        self.restore_s = restore_s
        self.state = {}
        self.shed_kw = {}
        self.manual_leases = {}
        self.events = []

    def update(self, elapsed_s, results, flexible_kw, network):
        events = []
        for target, lease in list(self.manual_leases.items()):
            if elapsed_s >= lease["expires_at_s"]:
                network.open_support(target)
                del self.manual_leases[target]
                events.append(self._event(elapsed_s, "manual_lease_expired", target))

        for panel, metrics in results["panels"].items():
            item = self.state.setdefault(panel, {
                "phase": "normal", "overload_since_s": None, "normal_since_s": None,
            })
            loading = metrics["line_loading_pct"] / 100
            if panel in self.manual_leases:
                continue

            if item["phase"] == "normal":
                if loading >= self.start_ratio:
                    if item["overload_since_s"] is None:
                        item["overload_since_s"] = elapsed_s
                    emergency = loading >= 1.0
                    sustained = elapsed_s - item["overload_since_s"] >= self.hold_s
                    if emergency or sustained:
                        tie = network.try_close_support(panel)
                        if tie is not None:
                            item["phase"] = "supporting"
                            events.append(self._event(elapsed_s, "support_enabled", panel, tie=tie))
                        elif flexible_kw.get(panel, 0) > self.shed_kw.get(panel, 0):
                            item["phase"] = "curtailing"
                            self._shed(panel, flexible_kw, elapsed_s, events)
                        else:
                            item["phase"] = "alert"
                            events.append(self._event(elapsed_s, "overload_unresolved", panel,
                                                      loading_pct=metrics["line_loading_pct"]))
                else:
                    item["overload_since_s"] = None
            elif loading >= self.start_ratio:
                item["normal_since_s"] = None
                if item["phase"] in ("supporting", "curtailing") and loading >= 1.0:
                    if flexible_kw.get(panel, 0) > self.shed_kw.get(panel, 0):
                        item["phase"] = "curtailing"
                        self._shed(panel, flexible_kw, elapsed_s, events)
                    elif item["phase"] != "alert":
                        item["phase"] = "alert"
                        events.append(self._event(elapsed_s, "overload_unresolved", panel,
                                                  loading_pct=metrics["line_loading_pct"]))
            else:
                if item["normal_since_s"] is None:
                    item["normal_since_s"] = elapsed_s
                elif elapsed_s - item["normal_since_s"] >= self.restore_s:
                    network.open_support(panel)
                    self.shed_kw[panel] = 0.0
                    item.update(phase="normal", overload_since_s=None, normal_since_s=None)
                    events.append(self._event(elapsed_s, "automatic_restore", panel))

        self.events.extend(events)
        return events

    def request_manual_support(self, donor, receiver, elapsed_s, lease_s, network):
        if not 0 < lease_s <= 3600:
            raise ValueError("manual support lease must be between 1 and 3600 seconds")
        tie = network.try_close_support(receiver, donor_panel=donor)
        if tie is None:
            raise ValueError("manual support would violate an electrical limit")
        self.manual_leases[receiver] = {
            "donor": donor,
            "expires_at_s": elapsed_s + lease_s,
            "command_id": str(uuid.uuid4()),
        }
        event = self._event(elapsed_s, "manual_support_enabled", receiver, donor=donor,
                            command_id=self.manual_leases[receiver]["command_id"], lease_s=lease_s)
        self.events.append(event)
        return event

    def _shed(self, panel, flexible_kw, elapsed_s, events):
        previous = self.shed_kw.get(panel, 0.0)
        amount = min(flexible_kw.get(panel, 0.0), previous + 0.25)
        self.shed_kw[panel] = amount
        events.append(self._event(elapsed_s, "flexible_load_reduced", panel,
                                  shed_kw=round(amount, 3)))

    @staticmethod
    def _event(elapsed_s, event, panel, **details):
        return {
            "event_id": str(uuid.uuid4()),
            "simulation_elapsed_s": elapsed_s,
            "event": event,
            "panel_id": panel,
            **details,
        }
