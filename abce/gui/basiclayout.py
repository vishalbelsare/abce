import os
import pandas as pd
from flexx import ui
from .dockpanel import DockPanel
from .make_graphs import (make_panel_graphs,
                          make_simple_graphs,
                          make_aggregate_graphs)
from .bokehwidget import BokehWidget
from abce.gui.webtext import abcedescription


def basiclayout(Form, simulation, title, top_bar=None, story={}, texts=[],
                pages=[], covertext=abcedescription, truncate_rounds=0):
    class Rex(ui.Widget):
        CSS = """
        h1, a {
            color: white;
            -webkit-margin-before: 0.20em;
            -webkit-margin-after: 0.0em;
            -webkit-margin-start: 1em;
            -webkit-margin-end: 1em;
            text-decoration: none;
        } """

        def init(self):
            self.first = True
            with ui.BoxLayout(orientation='v',
                              style="background-color: blue;"):
                with ui.HBox(flex=0):
                    ui.Label(text='<h1>%s</h1>' % title,
                             flex=1,
                             style="background-color: blue;")
                if top_bar is not None:
                    ui.Label(text=top_bar,
                             flex=0,
                             style="background-color: blue;")
                with DockPanel(flex=1) as self.dp:
                    form = Form(title='start',
                                style="location: W; overflow: scroll;")
                    for i in range(1, len(texts)):
                        ui.Label(title=texts[i].splitlines()[0],
                                 text='\n'.join(texts[i].splitlines()[1:]),
                                 style="location: A; overflow: scroll;",
                                 wrap=True)
                    for pagetitle, page in pages:
                        ui.IFrame(url=page,
                                  title=pagetitle,
                                  style="location: A; overflow: scroll;",)
                    ui.Label(title=covertext.splitlines()[0],
                             text='\n'.join(covertext.splitlines()[1:]),
                             style="location: R; overflow: scroll;",
                             wrap=True)

            @form.connect("run_simulation")
            def run_simulation(events):
                simulation(events['simulation_parameter'])
                self.display_results(events)

        def display_results(self, events):
            try:
                ignore_initial_rounds = int(events['ignore_initial_rounds'])
            except KeyError:
                ignore_initial_rounds = 100
            self.plots = []
            if self.first:
                self.plot_widgets = []
            try:
                path = events['subdir']
            except KeyError:
                path = newest_subdirectory('./result')

            i = 0
            for filename in os.listdir(path):
                if not filename.endswith('.csv'):
                    continue

                df = pd.read_csv(path + filename).ix[truncate_rounds:]
                try:
                    rounds = max(df['round'])
                except KeyError:
                    rounds = max(df['index'])
                if ignore_initial_rounds >= rounds:
                    ignore_initial_rounds = 0
                    print('abcegui.py ignore_initial_rounds >= rounds')
                if filename.startswith('aggregate_'):
                    title, plot = make_aggregate_graphs(
                        df, filename, ignore_initial_rounds)
                    self.plots.append(plot)
                else:
                    try:
                        if max(df.get('id', [0])) == 0:
                            title, plot = make_simple_graphs(
                                df, filename, ignore_initial_rounds)
                            self.plots.append(plot)
                        else:
                            title, plot = make_panel_graphs(
                                df, filename, ignore_initial_rounds)
                            self.plots.append(plot)
                    except ValueError:
                        print((filename, 'not displayable: ValueError'))

                if self.first:
                    with self.dp:
                        pw = BokehWidget(plot=plot,
                                         style="location: A",
                                         title=title)
                        self.plot_widgets.append(pw)
                else:
                    self.plot_widgets[i].plot = plot
                    i += 1

            self.first = False
    return Rex


def newest_subdirectory(directory='.'):
    directory = os.path.abspath(directory)
    all_subdirs = [os.path.join(directory, name)
                   for name in os.listdir(directory)
                   if os.path.isdir(os.path.join(directory, name))]
    return max(all_subdirs, key=os.path.getmtime) + '/'