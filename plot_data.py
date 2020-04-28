### Import packages ###
import pandas as pd

# Plotting
import plotly

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

def profile(df_plot, user_cell, user_cycle, user_x, user_y, user_y2):
    if user_cycle > 0 :
        df_slice = df_plot.loc[(user_cell, user_cycle)]
        user_cycle_out = user_cycle
    elif user_cycle == 0 :
        df_slice = df_plot.loc[user_cell]
        user_cycle_out = "all"

    fig = df_slice.iplot(
        asFigure=True,
        x=user_x,
        y=user_y,
        title='Profile: Cell {} - Cycle {}'.format(user_cell, user_cycle_out),
        xTitle="Test time (s)",
        yTitle="Voltage (V)",
        secondary_y=user_y2,
        secondary_y_title="Current (A)",
        width=2
    )

    return fig