from itertools import combinations
import random

import dash_cytoscape as cyto
import networkx as nx
import plotly.graph_objects as go
from dash import Dash, html, dcc, callback, Input, Output

from pdf import get_parsed_pdf, friends

data = get_parsed_pdf()

app = Dash()

# Define color mapping for minors
color_mapping = {
    "CyberSec": "#FF6347",
    "IHM": "#4682B4",
    "SSE": "#32CD32",
    "IF": "#FFD700",
    "IA-ID": "#8A2BE2",
    "IoT-CPS": "#FF69B4",
}

app.layout = [
    html.H5("Minor"),
    dcc.Dropdown(
        id='minor-dropdown',
        options=[{'label': availability, 'value': availability} for availability in data[0]['availability']],
        value=list(data[0]['availability'].keys()),
        multi=False
    ),

    html.H5("Courses in Common"),
    dcc.Graph(id='common-courses-graph'),

    html.H5("Lecturers"),
    dcc.Graph(id='lecturers-graph'),

    html.H5("Network Graph of Minors"),
    cyto.Cytoscape(
        id='network-graph',
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '600px'},
        elements=[],
        userZoomingEnabled=False,  # Disable zooming
        userPanningEnabled=False   # Disable panning
    )
]


@callback(
    Output('common-courses-graph', 'figure'),
    Input('minor-dropdown', 'value')
)
def update_common_courses_graph(selected_minor):
    # Filter courses for the selected minor
    minor_courses = [minor for minor in data if minor['availability'][selected_minor]]
    minor_courses_titles = [minor["title"] for minor in minor_courses]
    minor_hours = [(m["title"], m["cm_hours"] + m["td_hours"] + m["hne_hours"]) for m in minor_courses]

    # Find common courses with other minors
    common_courses = []
    for minor in [x for x in data[0]["availability"].keys() if x != selected_minor]:
        common_courses.append((
            minor,
            [m["title"] for m in data if m['availability'][minor] and m["title"] in minor_courses_titles]
        ))

    # Prepare nodes and links for Sankey diagram
    nodes = [selected_minor] + minor_courses_titles + [minor for minor, courses in common_courses if courses] + ["None"]
    node_indices = {node: idx for idx, node in enumerate(nodes)}

    links = {
        'source': [],
        'target': [],
        'value': []
    }

    # Links from selected minor to its courses
    for course, hours in minor_hours:
        links['source'].append(node_indices[selected_minor])
        links['target'].append(node_indices[course])
        links['value'].append(hours)

    # Links from courses to other minors sharing them or to "None"
    for course, hours in minor_hours:
        shared = False
        for minor, courses in common_courses:
            if course in courses:
                links['source'].append(node_indices[course])
                links['target'].append(node_indices[minor])
                links['value'].append(hours)
                shared = True
        if not shared:
            links['source'].append(node_indices[course])
            links['target'].append(node_indices["None"])
            links['value'].append(hours)

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes
        ),
        link=dict(
            source=links['source'],
            target=links['target'],
            value=links['value']
        )
    )])

    return fig


@callback(
    Output('lecturers-graph', 'figure'),
    Input('minor-dropdown', 'value')
)
def update_lecturers_graph(selected_minor):
    # Prepare data for the Sankey diagram
    minor_courses = [minor for minor in data if minor['availability'][selected_minor]]
    minor_courses_titles = [minor["title"] for minor in minor_courses]
    minor_hours = [(m["title"], m["cm_hours"] + m["td_hours"] + m["hne_hours"]) for m in minor_courses]
    lecturers_time = [(m["title"], m["in_charge"], m["email"], m["cm_hours"] + m["td_hours"] + m["hne_hours"]) for m in
                      minor_courses]

    # Extract email domains
    email_domains = [email.split('@')[-1] for _, _, email, _ in lecturers_time]

    # Prepare nodes and links for Sankey diagram
    nodes = [selected_minor] + minor_courses_titles + [lecturer for _, lecturer, _, _ in lecturers_time] + email_domains
    node_indices = {node: idx for idx, node in enumerate(nodes)}

    links = {
        'source': [],
        'target': [],
        'value': []
    }

    # Links from selected minor to its courses
    for course, hours in minor_hours:
        links['source'].append(node_indices[selected_minor])
        links['target'].append(node_indices[course])
        links['value'].append(hours)

    # Links from courses to lecturers
    for course, lecturer, _, hours in lecturers_time:
        links['source'].append(node_indices[course])
        links['target'].append(node_indices[lecturer])
        links['value'].append(hours)

    # Links from lecturers to email domains
    for _, lecturer, email, hours in lecturers_time:
        email_domain = email.split('@')[-1]
        links['source'].append(node_indices[lecturer])
        links['target'].append(node_indices[email_domain])
        links['value'].append(hours)

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes
        ),
        link=dict(
            source=links['source'],
            target=links['target'],
            value=links['value']
        )
    )])

    return fig


@callback(
    Output('network-graph', 'elements'),
    Input('minor-dropdown', 'value')
)
def update_network_graph(selected_minor):
    # Prepare data for the network graph
    G = nx.Graph()

    for minor in data[0]['availability']:
        G.add_node(minor)

    # Add nodes for each minor
    for lesson in data:
        # for each couple of minors
        for minor1, minor2 in combinations(lesson['availability'], 2):
            if lesson['availability'][minor1] and lesson['availability'][minor2]:
                if G.has_edge(minor1, minor2):
                    G[minor1][minor2]['weight'] += (lesson['cm_hours'] + lesson['td_hours'] + lesson['hne_hours'])
                else:
                    G.add_edge(minor1, minor2, weight=(lesson['cm_hours'] + lesson['td_hours'] + lesson['hne_hours']))

    # remove minor nodes that don't have any student
    G.remove_nodes_from([node for node in G.nodes if node not in friends.values()])

    # Add people nodes and connect to their minor
    for person, minor in friends.items():
        G.add_node(person)
        G.add_edge(person, minor, weight=1)  # Connect person to their minor

    # remove minor nodes that are not neighbors of the selected minor
    G.remove_nodes_from([node for node in G.nodes if
                         not G.has_edge(selected_minor, node) and node not in friends and node != selected_minor])

    # remove orphan nodes
    G.remove_nodes_from(list(nx.isolates(G)))

    # Create nodes and edges for Cytoscape
    pos = nx.circular_layout(G)  # Position nodes in a circle
    elements = []
    for node in G.nodes:
        color = color_mapping.get(friends.get(node, node), '#888')  # Default color if minor not in color_mapping
        size = 50 if node in friends else 100  # Smaller size for people nodes
        elements.append({
            'data': {'id': node, 'label': node},
            'position': {
                'x': pos[node][0] * 1000 + random.uniform(-100, 100) if node in friends else pos[node][0] * 1000,
                'y': pos[node][1] * 1000 + random.uniform(-100, 100) if node in friends else pos[node][1] * 1000
            },
            'style': {'background-color': color, 'width': size, 'height': size}
        })
    for edge in G.edges(data=True):
        edge_color = '#FF0000' if selected_minor in edge else '#888'
        elements.append({
            'data': {
                'source': edge[0],
                'target': edge[1],
                'weight': edge[2]['weight']
            },
            'style': {
                'width': edge[2]['weight'] / 20,  # Adjust the divisor to scale the width appropriately
                'line-color': edge_color
            }
        })

    return elements


if __name__ == '__main__':
    app.run(debug=True)
