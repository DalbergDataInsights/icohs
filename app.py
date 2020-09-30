# from COC_dashboard import data_story
# from demo_v1 import data_story

import sys

sys.path.insert(0, "./coc-dashboard")

from view import ds  # NOQA: E402

server = ds.app.server

from callbacks import define_callbacks

define_callbacks(ds)

if __name__ == "__main__":
    ds.run(dev=True)
else:
    ds.set_layout_and_callbacks()
