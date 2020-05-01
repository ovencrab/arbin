### Import packages ###
import pandas as pd
import numpy as np
import re
import sys

# Plotting
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Cufflinks wrapper on plotly
import cufflinks as cf

# Offline mode
from plotly.offline import iplot
cf.go_offline()

# Set global theme
cf.set_config_file(world_readable=True, theme='ggplot')

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
### Functions ###
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

def fprofile(df_plot, user_cell, user_cycle, user_x, user_y, user_y2):
    if user_cycle > 0 :
        df_slice = df_plot.loc[(user_cell, user_cycle)]
        user_cycle_out = user_cycle
    elif user_cycle == 0 :
        df_slice = df_plot.loc[user_cell]
        user_cycle_out = "all"


    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_slice[user_x].values,
                             y=df_slice[user_y].values,
                             mode='lines',
                             name='Voltage (V)'),
                            secondary_y=False)

    fig.add_trace(go.Scatter(x=df_slice[user_x].values,
                             y=df_slice[user_y2].values,
                             mode='lines',
                             name='Current (A)'),
                            secondary_y=True)

    fig.update_layout(title='Profile: Cell {} - Cycle {}'.format(user_cell, user_cycle_out), xaxis_title='Test time (s)')
    fig.update_yaxes(title_text="Voltage (V)", secondary_y=False)
    fig.update_yaxes(title_text="Current (A)", secondary_y=True)

    return fig


def cycle_trace(df_cap, fig, n, user_cap_type, user_cyc_y) :
    idx = pd.IndexSlice
    fig.add_trace(go.Scatter(x=df_cap.index.get_level_values(1),
                             y=np.squeeze(df_cap.loc[idx[n, :],
                                                      idx[user_cap_type, user_cyc_y]].values),
                             mode='markers', name='Cell {}'.format(n)))

    return fig


def def_format(fig, n, n_cells) :
    # Generate graph title
    if n_cells == 1 and n > 0 :
        user_cell_out = n
    elif n == 0 :
        user_cell_out = 'mean'
    else :
        user_cell_out = '1-{}'.format(n_cells)

    fig.update_layout(title='Cell {} - Cycles'.format(user_cell_out),
                    xaxis_title='Cycle',
                    yaxis_title='Capacity (Ah)')
    fig.update_xaxes(showgrid=False, rangemode='tozero')
    fig.update_yaxes(showgrid=False, rangemode='tozero')

    fig.show()


def cycle_old(df_cap, user_cell, user_cycle, user_cyc_x, user_cyc_y, user_cyc_y2):
    idx = pd.IndexSlice
    # Filter dataframe by user_cycle entry
    if user_cycle == 0 :
        df_plot = df_cap
        user_cycle_out = 'all'
    elif type(user_cycle) == int and user_cycle > 0 :
        df_plot = df_cap.loc(axis=0)[:, user_cycle]
        user_cycle_out = user_cycle
    elif type(user_cycle) == str :
        try :
            values = [int(s) for s in re.findall(r'\b\d+\b', user_cycle)]
            df_plot = df_cap.loc[idx[:, values[0]:values[1]],:]
            user_cycle_out = user_cycle
        except :
            print('Format error in ''Cycles'' input field')


    # Filter dataframe by user_cell entry
    if user_cell == 0 :
        df_plot = df_plot.xs(0, level='cell', drop_level=False)
        user_cell_out = 'Mean'
    elif type(user_cell) == int and user_cell > 0:
        df_plot = df_plot.xs(user_cell, level='cell', drop_level=False)
        user_cell_out = user_cell
    elif type(user_cell) == str :
        try :
            values = [int(s) for s in re.findall(r'\b\d+\b', user_cell)]
            df_plot = df_plot.loc[idx[values[0]:values[1],:],:]
            user_cell_out = user_cell
        except :
            print('Format error in ''Cells'' input field')


    #  Plot with or without second y axis
    if user_cyc_y2 == 0 :
        fig = go.Figure()

        for n in df_plot.index.get_level_values(0).unique() :
            fig.add_trace(go.Scatter(x=df_plot.index.get_level_values(1),
                                y=np.squeeze(df_plot.loc[idx[n, :], idx[:, user_cyc_y]].values),
                                mode='markers',
                                name='Cell {}'.format(n)))

        fig.update_layout(yaxis_title='Capacity (Ah)')
    else :
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(go.Scatter(x=df_plot.index.get_level_values(1),
                                y=np.squeeze(df_plot.loc(axis=1)[:, user_cyc_y].values),
                                mode='markers',
                                name='capacity'),
                                secondary_y=False)

        fig.add_trace(go.Scatter(x=df_plot.index.get_level_values(1),
                                y=np.squeeze(df_plot.loc(axis=1)[:, user_cyc_y2].values),
                                mode='markers',
                                name='cou_eff'),
                                secondary_y=True)

        fig.update_yaxes(title_text="Voltage (V)", secondary_y=False)
        fig.update_yaxes(title_text="Current (A)", secondary_y=True)


    fig.update_layout(title='Profile: Cell {} - Cycle {}'.format(user_cell_out,user_cycle_out),
                    xaxis_title='Cycle')
    fig.update_xaxes(showgrid=False, rangemode='tozero')
    fig.update_yaxes(showgrid=False, rangemode='tozero')

    return fig

##### Using cufflinks #####
# def fprofile(df_plot, user_cell, user_cycle, user_x, user_y, user_y2):
#     if user_cycle > 0 :
#         df_slice = df_plot.loc[(user_cell, user_cycle)]
#         user_cycle_out = user_cycle
#     elif user_cycle == 0 :
#         df_slice = df_plot.loc[user_cell]
#         user_cycle_out = "all"

#     fig = df_slice.iplot(
#         asFigure=True,
#         x=user_x,
#         y=user_y,
#         title='Profile: Cell {} - Cycle {}'.format(user_cell, user_cycle_out),
#         xTitle="Test time (s)",
#         yTitle="Voltage (V)",
#         secondary_y=user_y2,
#         secondary_y_title="Current (A)",
#         width=2
#     )

#     return fig