# risk.py

def compute_risk_scores(
graph,
critical_scores
):
    risks = {}

    for node in graph.nodes():

        stress = (
            graph.nodes[node]["stress"]
        )

        load_ratio = (
            graph.nodes[node]["load"]
            /
            graph.nodes[node]["capacity"]
        )

        criticality = (
            critical_scores.get(
                node,
                0
            )
        )

        risk = (
            0.5 * stress
            +
            0.3 * criticality
            +
            0.2 * load_ratio
        )

        risks[node] = min(
            risk,
            1.0
        )

    return risks

