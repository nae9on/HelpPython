import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation


ReferenceTime: np.datetime64 = np.datetime64('2021-08-18T00:00:00.000000000')


class XlsParser:

    def __init__(self, filename: str):
        self.filename: str = filename
        self.time = None
        self.millisecond = None
        self.status = None
        self.time_delta = None
        self.sampled_timeline = None
        self.sampled_status = None
        self.parse_file()

    def parse_file(self):
        data = pd.ExcelFile(self.filename)
        sheet = data.parse(0)
        self.time = sheet['tijdstip'].to_numpy()
        self.millisecond = sheet['msec'].to_numpy()
        self.status = sheet['status'].to_numpy()

        # Get the time delta
        dt = (self.time - ReferenceTime)
        dt = dt / 1e+6  # convert ns to ms
        self.time_delta = dt + self.millisecond
        self.time_delta = self.time_delta.astype(int)

        self.sampled_timeline = np.arange(0, self.time_delta[-1] + 1, 1)
        self.sampled_status = np.zeros((self.sampled_timeline.size,), dtype=np.int)
        self.sampled_status[0: self.time_delta[0]] = -1
        self.sampled_status[self.time_delta] = self.status
        for itr in range(0, self.time_delta.size - 2, 1):
            self.sampled_status[self.time_delta[itr] + 1: self.time_delta[itr + 1]] = self.status[itr]


if __name__ == "__main__":
    Reference_LA1 = XlsParser("./FinalLogs/LA1/RawDetectors_LA1_18-20_082021.xls")
    TrafiCamAI_LA1 = XlsParser("./FinalLogs/LA1/RawDetectors_TCA1_18-20_082021.xls")
    TrafiOne_LA1 = XlsParser("./FinalLogs/LA1/RawDetectors_TOA1_18-20_082021.xls")

    Reference_LA = XlsParser("./FinalLogs/LA/RawDetectors_LA_18-20_082021.xls")
    TrafiCamAI_LA = XlsParser("./FinalLogs/LA/RawDetectors_TCA_18-20_082021.xls")

    Reference = Reference_LA1
    Result = TrafiCamAI_LA1

    # Trim the timelines to valid range
    min_index = max(Reference.time_delta[0], Result.time_delta[0])
    max_index = min(Reference.time_delta[-1], Result.time_delta[-1])

    TP = (Reference.sampled_status[min_index: max_index] == 1) & (Result.sampled_status[min_index: max_index] == 1)
    FP = (Reference.sampled_status[min_index: max_index] == 0) & (Result.sampled_status[min_index: max_index] == 1)
    FN = (Reference.sampled_status[min_index: max_index] == 1) & (Result.sampled_status[min_index: max_index] == 0)
    TN = (Reference.sampled_status[min_index: max_index] == 0) & (Result.sampled_status[min_index: max_index] == 0)

    Precision = np.sum(TP) / (np.sum(TP) + np.sum(FP))
    Sensitivity = np.sum(TP) / (np.sum(TP) + np.sum(FN))

    print("Precision", Precision)
    print("Sensitivity", Sensitivity)
    print("End")

    # Plotting
    # https://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
    window_length_minutes = 30

    window_length_ms = window_length_minutes * 60 * 1000
    time_shift_ms = 60000

    fig = plt.figure(figsize=(20, 2))
    ax = plt.axes(xlim=(0, window_length_ms), ylim=(-2, 2))
    line, = ax.plot([], [], lw=1, color='k')
    line2, = ax.plot([], [], lw=1, color='r')
    label = ax.text(2, 1.5, '', ha='left', va='center', fontsize=10, color="Red")

    # initialization function: plot the background of each frame
    def init():
        line.set_data([], [])
        line2.set_data([], [])
        label.set_text('')
        return line, line2, label

    def animate(i):
        t_begin = int(i*time_shift_ms)
        t_end = int(i*time_shift_ms+window_length_ms)
        # print(t_begin, t_end)
        x = np.arange(0, window_length_ms)
        y = Reference.sampled_status[t_begin:t_end]
        y2 = Result.sampled_status[t_begin:t_end]
        line.set_data(x, y)
        line2.set_data(x, y2)
        label.set_text(str(t_begin)+str('-')+str(t_end))
        return line, line2, label

    plot_animation = True

    if plot_animation:
        anim = animation.FuncAnimation(fig=fig, func=animate, frames=int(Reference.sampled_timeline.size/time_shift_ms),
                                       init_func=init, interval=200, blit=True)
        anim.save('./timeline.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
        # plt.show()


# def count_consecutive(arr, n):
#     # pad a with False at both sides for edge cases when array starts or ends with n
#     d = np.diff(np.concatenate(([False], arr == n, [False])).astype(int))
#     # subtract indices when value changes from False to True from indices where value changes from True to False
#     return np.flatnonzero(d == -1) - np.flatnonzero(d == 1)


# sum(count_consecutive(Reference.status, 1) > 1)
