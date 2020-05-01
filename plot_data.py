### Import packages ###
import pandas as pd
import re

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

def cap(df_cap, user_cell, user_cycle, user_x_cyc, user_y_cyc, user_y2_cyc):

    if user_cycle == 0 :
        pass
    elif user_cycle > 0 and type(user_cycle) == int :
        df_plot = df_cap.loc(axis=0)[:, user_cycle]
    elif type(user_cycle) == str :
        try :
            values = [int(s) for s in re.findall(r'\b\d+\b', user_cycle)]
            df_plot = df_cap.loc(axis=0)[:, values[0]:values[1]]
        except :
            print('Format error in ''Cycles'' input field')

    if user_cell == 0 :
        df_plot = df_plot.groupby('cycle_index').mean()
    elif user_cell > 0 and type(user_cell) == int :
        df_plot = df_plot.loc[user_cell]
    elif type(user_cell) == str :
        try :
            values = [int(s) for s in re.findall(r'\b\d+\b', user_cell)]
            df_plot = df_plot.loc[values[0]:values[1]]
        except :
            print('Format error in ''Cells'' input field')

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df_plot[user_x_cyc].values,
                             y=df_plot[user_y_cyc].values,
                             mode='lines',
                             name='Voltage (V)'),
                            secondary_y=False)
    fig.add_trace(go.Scatter(x=df_plot[user_x_cyc].values,
                             y=df_plot[user_y2_cyc].values,
                             mode='lines',
                             name='Current (A)'),
                            secondary_y=True)
    fig.update_layout(title='Profile: Cell {} - Cycle {}'.format(user_cell, user_cycle_out), xaxis_title='Test time (s)')
    fig.update_yaxes(title_text="Voltage (V)", secondary_y=False)
    fig.update_yaxes(title_text="Current (A)", secondary_y=True)

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