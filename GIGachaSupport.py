import datetime
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import colors
import time
import tkinter as tk
from tkinter import filedialog, TclError, messagebox
import traceback


def sim(IntertwinedFateNum, Discounts, KrAu, KrAuEx, ExpectedCharacterNum, CharacterPoolGuarantee, CharacterPoolStage,
        ExpectedWeaponNum, WeaponPoolGuarantee, WeaponPoolStage, BindingNum, CatchLight):
    start = time.time()
    # 拥有的纠缠之缘数量
    # 抽卡消耗比例
    IntertwinedFateNum = int(IntertwinedFateNum / Discounts)

    # 预算
    # ------------------------- 下为角色池部分 -------------------------
    # 期望抽到角色数（0-7）
    # 当前是否大保底（True/False）
    # 角色池的水位（0-89）
    # ------------------------- 下为武器池部分 -------------------------
    # 期望抽到武器数（0-5）
    # 当前是否大保底（True/False）
    # 武器池的水位（0-79）
    # 命定值（0-2）
    output = []

    # 单次抽卡的概率
    # 角色池
    def percent_character(s):
        if s <= 73:
            return 0.006
        elif s <= 89:
            return 0.006 + 0.06 * (s - 73)
        else:
            return 1

    # 武器池
    def percent_weapon(s):
        if s <= 62:
            return 0.007
        elif s <= 73:
            return 0.007 + 0.07 * (s - 62)
        elif s <= 79:
            return 0.777 + 0.035 * (s - 73)
        else:
            return 1

    # 初始化一个零矩阵
    size = 630 * ExpectedCharacterNum + 240 * ExpectedWeaponNum + 1  # 这里加上1是为了让最后一行表示达成抽卡预期的状态
    TPmatrix = np.zeros((size, size))
    # 角色池的初始状态设置
    CharacterPoolOffset = 0
    if ExpectedCharacterNum != 0:
        if not CharacterPoolGuarantee:
            CharacterPoolOffset = CharacterPoolStage
        elif CharacterPoolGuarantee and CatchLight != 3:
            CharacterPoolOffset = CharacterPoolStage + 90
        CharacterPoolOffset += CatchLight * 180
    # 生成转移概率矩阵（矩阵前面的行是武器，后面的行是角色，最后一行表示的状态是已经达成抽卡预期）
    # 这一部分代码生成抽武器的状态，如果要抽的武器数为0，那么就不会运行这一部分代码
    for i in range(0, ExpectedWeaponNum):
        offset = 240 * i
        # 小保底/命定0
        for j in range(0, 80):
            x = j % 80 + 1
            if i == ExpectedWeaponNum - 1:
                # 该行属于要抽的最后一把武器的部分，那么如果出限定就会进入角色部分，要加上角色池的初始偏移量
                TPmatrix[offset + j, offset + 240 + CharacterPoolOffset] = percent_weapon(x) * 0.375
            else:
                # 该行不属于要抽的最后一把武器的部分，那么抽完会进入下一把武器
                TPmatrix[offset + j, offset + 240] = percent_weapon(x) * 0.375
            TPmatrix[offset + j, offset + 160] = percent_weapon(x) * 0.625
            TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        # 大保底/命定0
        for j in range(80, 160):
            x = j % 80 + 1
            if i == ExpectedWeaponNum - 1:
                TPmatrix[offset + j, offset + 240 + CharacterPoolOffset] = percent_weapon(x) * 0.5
            else:
                TPmatrix[offset + j, offset + 240] = percent_weapon(x) * 0.5
            TPmatrix[offset + j, offset + 80] = percent_weapon(x) * 0.5
            # 在p159状态下抽卡必定成功，故一定会转移到p160状态，这里加上条件判断是为了避免覆盖前面的代码
            if j != 159:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)
        # 命定1
        for j in range(160, 240):
            x = j % 80 + 1
            if i == ExpectedWeaponNum - 1:
                TPmatrix[offset + j, offset + 240 + CharacterPoolOffset] = percent_weapon(x)
            else:
                TPmatrix[offset + j, offset + 240] = percent_weapon(x)
            if j != 239:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_weapon(x)

    # 这一部分代码生成抽角色的状态，如果要抽的角色数为0，那么就不会运行这一部分代码
    for i in range(0, ExpectedCharacterNum):
        offset = 630 * i + ExpectedWeaponNum * 240
        # 小保底，明光0
        for j in range(0, 90):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 630] = percent_character(x) * 0.5
            TPmatrix[offset + j, offset + 90] = percent_character(x) * 0.5
            if j != 89:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 大保底，明光1
        for j in range(90, 180):
            x = j % 90 + 1
            TPmatrix[offset + j, min(size - 1, offset + 810)] = percent_character(x)
            if j != 179:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 小保底，明光1
        for j in range(180, 270):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 630] = percent_character(x) * 0.5
            TPmatrix[offset + j, offset + 270] = percent_character(x) * 0.5
            if j != 269:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 大保底，明光2
        for j in range(270, 360):
            x = j % 90 + 1
            TPmatrix[offset + j, min(size - 1, offset + 990)] = percent_character(x)
            if j != 359:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 小保底，明光2
        for j in range(360, 450):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 630] = percent_character(x) * 0.75
            TPmatrix[offset + j, offset + 450] = percent_character(x) * 0.25
            if j != 449:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 大保底，明光3，50%捕获明光
        for j in range(450, 540):
            x = j % 90 + 1
            TPmatrix[offset + j, min(size - 1, offset + 1170)] = percent_character(x)
            if j != 539:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)
        # 必触发捕获明光
        for j in range(540, 630):
            x = j % 90 + 1
            TPmatrix[offset + j, offset + 630] = percent_character(x)
            if j != 629:
                TPmatrix[offset + j, offset + j + 1] = 1 - percent_character(x)

    # 最后一行表示已经达成抽卡预期，所以从该状态到其他状态的概率都是0，到自身的概率为1
    TPmatrix[size - 1, size - 1] = 1

    # 生成初始状态向量，如果抽武器，那么和武器池水位有关，否则和角色池水位有关
    initVector = np.zeros(size)

    if ExpectedWeaponNum != 0:
        if BindingNum == 0:
            if not WeaponPoolGuarantee:
                initVector[WeaponPoolStage] = 1
            elif WeaponPoolGuarantee:
                initVector[WeaponPoolStage + 80] = 1
        elif BindingNum == 2:
            initVector[WeaponPoolStage + 160] = 1
    else:  # 这里是不抽武器的情况，和角色池水位有关
        initVector[CharacterPoolOffset] = 1

    # 存储达到10%、25%、50%、75%、90%概率时的抽数
    percent10num = 0
    percent25num = 0
    percent50num = 0
    percent75num = 0
    percent90num = 0
    percentlist = [0]

    # 存储达到预期次数的概率
    resultVector = initVector
    result = 0
    i = 0

    while result < 0.999:
        # 将初始状态向量和转移概率矩阵不断相乘，相乘的次数为抽数，得到预期次数后状态的概率分布
        i += 1
        resultVector = resultVector @ TPmatrix
        result = resultVector[size - 1]
        percentlist.append(result)
        if result > 0.1 and percent10num == 0:
            percent10num = i + 1
        if result > 0.25 and percent25num == 0:
            percent25num = i + 1
        if result > 0.5 and percent50num == 0:
            percent50num = i + 1
        if result > 0.75 and percent75num == 0:
            percent75num = i + 1
        if result > 0.9 and percent90num == 0:
            percent90num = i + 1

    # 创建概率曲线图
    plt.close()  # 关闭已存在图表
    plt.rcParams['font.sans-serif'] = ['SimHei']
    fig, ax = plt.subplots()
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.025))

    # 设定横轴间距
    if len(percentlist) > 500:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(50 * int(len(percentlist) / 250)))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(12.5 * int(len(percentlist) / 250)))
    elif len(percentlist) > 200:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(12.5))
    elif len(percentlist) > 80:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(20))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))
    elif len(percentlist) > 30:
        ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(2.5))

    # 描点画图
    ax.set_title('原神抽卡成功率分布')
    ax.grid(True)
    plt.plot(percentlist)
    plt.xlim(xmin=0, xmax=len(percentlist) + 5)
    plt.ylim(ymin=0, ymax=1)

    # 不额外氪金时标出此时函数上的点
    position = int(IntertwinedFateNum / Discounts)
    if len(percentlist) > IntertwinedFateNum:
        possibility = percentlist[position]
    else:
        possibility = 1

    plt.vlines(x=position, ymin=0, ymax=possibility, label='不氪', linestyles='dashed', color='blue')
    plt.hlines(y=possibility, xmin=0, xmax=position, label='', linestyles='dashed', color='blue')
    output.append(f'不氪金成功率为{possibility * 100:.1f}%')

    # 首充计算
    FirstEx = int(KrAu / 8)
    if FirstEx:
        if len(percentlist) > IntertwinedFateNum + FirstEx / Discounts:
            position = int(IntertwinedFateNum + FirstEx / Discounts)
            possibility = percentlist[position]
            plt.vlines(x=position, ymin=0, ymax=possibility, label='首充', linestyles='dashed', color='green')
            plt.hlines(y=possibility, xmin=0, xmax=position, label='', linestyles='dashed', color='green')
        else:
            possibility = 1
        output.append(f'氪完首充后成功率为{possibility * 100:.1f}%')

    # 额外氪金计算
    cols = generate_gradient_colors(int(KrAuEx / 648), 'gold', 'red')  # 生成渐变色标识
    for i in range(int(KrAuEx / 648)):
        if len(percentlist) > IntertwinedFateNum + (50.5 * (i + 1) + FirstEx) / Discounts:
            position = int(int(IntertwinedFateNum + (50.5 * (i + 1) + FirstEx) / Discounts))
            possibility = percentlist[position]
            plt.vlines(x=position, ymin=0, ymax=possibility, label=f'氪{i + 1}单', linestyles='dashed', color=cols[i])
            plt.hlines(y=possibility, xmin=0, xmax=position, label='', linestyles='dashed', color=cols[i])
        else:
            possibility = 1
        output.append(f'额外氪{i + 1}个648后成功率为{possibility * 100:.1f}%')

    # 设置 Y 轴格式为百分比
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1.0))
    ax.legend(loc='upper left')
    output.append(f'模拟用时{time.time() - start:.3f}秒')
    return output, fig


def generate_gradient_colors(n, start='#FFFFFF', end='#000000'):  # 生成渐变色列表
    start_color = colors.to_rgb(start)
    end_color = colors.to_rgb(end)
    return [
        (
            start_color[0] + (end_color[0] - start_color[0]) * i / (n - 1),
            start_color[1] + (end_color[1] - start_color[1]) * i / (n - 1),
            start_color[2] + (end_color[2] - start_color[2]) * i / (n - 1)
        )
        for i in range(n)
    ]


# 获取软件图标
def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)  # 打包环境下获取当前路径
    return filename  # 开发环境直接使用根目录


# 定义一个假类型避免初始化窗口时报错
class Dummy:
    @staticmethod
    def winfo_exists():
        return False

    @staticmethod
    def destroy():
        return

    @staticmethod
    def get_tk_widget():
        return Dummy()


# 用户取消确认操作时抛出的异常
class UserCancelledError(Exception):
    pass


# 图标路径
icon_path = resource_path("GIGachaSupport.ico")

# 初始化图表
figure = Figure()
canvas = Dummy()
fig_win = Dummy()


def main():
    # 定义关闭事件的处理函数
    def on_closing():
        plt.close('all')  # 关闭所有的 matplotlib 图表
        root.destroy()  # 关闭 Tkinter 窗口

    def textbox_output(result):
        result_text.config(state=tk.NORMAL)  # 设置为可编辑状态
        result_text.insert(tk.END, f"{result}\n")
        result_text.see(tk.END)
        result_text.config(state=tk.DISABLED)  # 设置为只读状态

    def clear_textbox():
        global figure, canvas, fig_win
        result_text.config(state=tk.NORMAL)  # 设置为可编辑状态
        result_text.delete('1.0', tk.END)  # 清空文本框内容
        result_text.config(state=tk.DISABLED)  # 设置为只读状态
        # 重新初始化图表
        figure = Figure()
        canvas = Dummy()
        fig_win = Dummy()

    # 外层函数，用于转移参数启动模拟
    def sim_shell():
        global figure
        result = []
        try:
            if not int(IntertwinedFateNum.get() if IntertwinedFateNum.get() else 0.0) + int(
                    int(Primo.get()) / 160 if Primo.get() else 0.0):
                raise ValueError("无可用抽数")
            elif not 0 < float(Discounts.get() if Discounts.get() else 1.0) <= 1:
                raise ValueError("抽卡消耗系数只能在(0,1]区间内")
            elif not int(ExpectedCharacterNum.get() if ExpectedCharacterNum.get() else 0.0) + int(
                    ExpectedWeaponNum.get() if ExpectedWeaponNum.get() else 0.0):
                raise ValueError("无抽取目标")
            elif int(ExpectedCharacterNum.get() if ExpectedCharacterNum.get() else 0.0) * 630 + int(
                    ExpectedWeaponNum.get() if ExpectedWeaponNum.get() else 0.0) * 240 > 5000:
                confirm = messagebox.askyesno("", "当前配置模拟耗时可能较长，请确认是否继续")
                if not confirm:
                    raise UserCancelledError
            result, figure = sim(int(IntertwinedFateNum.get() if IntertwinedFateNum.get() else 0.0) + int(
                int(Primo.get()) / 160 if Primo.get() else 0.0),
                                 float(Discounts.get() if Discounts.get() else 1.0),
                                 int(KrAu.get() if KrAu.get() else 0.0),
                                 int(KrAuEx.get() if KrAuEx.get() else 0.0),
                                 int(ExpectedCharacterNum.get() if ExpectedCharacterNum.get() else 0.0),
                                 bool(checkbox_1.get()),
                                 int(CharacterPoolStage.get() if CharacterPoolStage.get() else 0.0),
                                 int(ExpectedWeaponNum.get() if ExpectedWeaponNum.get() else 0.0),
                                 bool(checkbox_2.get()),
                                 int(WeaponPoolStage.get() if WeaponPoolStage.get() else 0.0),
                                 slider_value1.get(), slider_value2.get())
        except ValueError as e:
            if str(e):
                result.append(str(e))
            result.append("输入无效")
        except UserCancelledError:
            result.append("已取消模拟")
        except Exception as e:
            messagebox.showerror("未知错误", f"发生以下错误\n{e}\n请查看输出框并联系开发者")
            result.append(traceback.format_exc())

        for item in result:
            # 依次输出文字结论
            textbox_output(item)

    # 显示图表
    def show_plot():
        global figure, canvas, fig_win

        # 当前图表并非为空
        if figure.axes:
            if canvas is not None:
                canvas.get_tk_widget().destroy()

            # 如果窗口已经存在，先关闭它
            if fig_win.winfo_exists():
                fig_win.destroy()

            # 创建一个新的窗口
            fig_win = tk.Toplevel(root)

            # 设置子窗口图标和名称
            try:
                fig_win.iconbitmap(icon_path)
            except TclError:
                pass
            finally:
                fig_win.title("概率曲线图")
                fig_win.resizable(False, False)

            # 嵌入图像
            canvas = FigureCanvasTkAgg(figure, master=fig_win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # 添加保存按钮
            btn_save = tk.Button(fig_win, text="保存图像", command=save_figure)
            btn_save.pack(pady=10)

        else:
            textbox_output("当前没有数据")

    def save_figure():
        global figure

        # 生成默认文件名
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        default_filename = f"result {timestamp}.png"

        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG 图像", "*.png"), ("所有文件", "*.*")],
            initialfile=default_filename,
            title="保存图像"
        )

        # 如果用户选择了文件路径，保存图像
        if file_path:
            figure.savefig(file_path)
            textbox_output(f"图像已保存到: {file_path}")

    # 创建主窗口，设置图标和名称
    root = tk.Tk()
    try:
        root.iconbitmap(icon_path)
    except TclError:
        pass
    finally:
        root.title("原神抽卡模拟器")
        root.geometry("576x576")
        root.resizable(False, False)

    # 设置窗口元素
    tk.Label(root, text="纠缠之缘数量:").grid(row=0, column=0, padx=5, pady=5)
    IntertwinedFateNum = tk.Entry(root)
    IntertwinedFateNum.grid(row=1, column=0, padx=5, pady=5)

    tk.Label(root, text="原石数量:").grid(row=0, column=1, padx=5, pady=5)
    Primo = tk.Entry(root)
    Primo.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(root, text="抽卡消耗比例(默认:1):").grid(row=0, column=2, padx=5, pady=5)
    Discounts = tk.Entry(root)
    Discounts.grid(row=1, column=2, padx=5, pady=5)

    tk.Label(root, text="期望抽到的角色数量:").grid(row=2, column=0, padx=5, pady=5)
    ExpectedCharacterNum = tk.Entry(root)
    ExpectedCharacterNum.grid(row=3, column=0, padx=5, pady=5)

    checkbox_1 = tk.BooleanVar()
    CharacterPoolGuarantee = tk.Checkbutton(root, text="角色池是否大保底", variable=checkbox_1)
    CharacterPoolGuarantee.grid(row=3, column=1, padx=5, pady=5)

    tk.Label(root, text="角色池水位:").grid(row=2, column=2, padx=5, pady=5)
    CharacterPoolStage = tk.Entry(root)
    CharacterPoolStage.grid(row=3, column=2, padx=5, pady=5)

    tk.Label(root, text="期望抽到的武器数量:").grid(row=4, column=0, padx=5, pady=5)
    ExpectedWeaponNum = tk.Entry(root)
    ExpectedWeaponNum.grid(row=5, column=0, padx=5, pady=5)

    checkbox_2 = tk.BooleanVar()
    WeaponPoolGuarantee = tk.Checkbutton(root, text="武器池是否大保底", variable=checkbox_2)
    WeaponPoolGuarantee.grid(row=5, column=1, padx=5, pady=5)

    tk.Label(root, text="武器池水位:").grid(row=4, column=2, padx=5, pady=5)
    WeaponPoolStage = tk.Entry(root)
    WeaponPoolStage.grid(row=5, column=2, padx=5, pady=5)

    tk.Label(root, text="首充氪金预算(RMB):").grid(row=6, column=0, padx=5, pady=5)
    KrAu = tk.Entry(root)
    KrAu.grid(row=7, column=0, padx=5, pady=5)

    tk.Label(root, text="额外氪金预算(RMB):").grid(row=6, column=2, padx=5, pady=5)
    KrAuEx = tk.Entry(root)
    KrAuEx.grid(row=7, column=2, padx=5, pady=5)

    tk.Label(root, text="命定值:").grid(row=8, column=0, padx=5, pady=5)
    slider_value1 = tk.IntVar()
    BindingNum = tk.Scale(root, from_=0, to=1, orient=tk.HORIZONTAL, variable=slider_value1)
    BindingNum.grid(row=9, column=0, padx=5, pady=5)

    tk.Label(root, text="已歪次数:").grid(row=8, column=2, padx=5, pady=5)
    slider_value2 = tk.IntVar()
    CatchLight = tk.Scale(root, from_=0, to=3, orient=tk.HORIZONTAL, variable=slider_value2)
    CatchLight.grid(row=9, column=2, padx=5, pady=5)

    button_sim = tk.Button(root, text="模拟", command=sim_shell)
    button_sim.grid(row=10, column=0, padx=5, pady=5)

    button_show_plot = tk.Button(root, text="生成概率曲线图", command=show_plot)
    button_show_plot.grid(row=10, column=1, padx=5, pady=5)

    button_clear = tk.Button(root, text="清空结果", command=clear_textbox)
    button_clear.grid(row=10, column=2, padx=5, pady=5)

    result_text = tk.Text(root, height=12, state='normal')
    result_text.grid(row=11, column=0, padx=5, pady=5, columnspan=3)
    result_text.config(state=tk.DISABLED)

    # 确保完全关闭
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 启动程序
    root.mainloop()


if __name__ == '__main__':
    main()
