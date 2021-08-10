import pandas as pd
import matplotlib.pyplot as plt
 

def show_box_plot(df):
    boxes = []
    labels = []
    for day in range(1, 6):
        boxes.append(df.loc[df['每周几'] == day]['收益率'])
        labels.append(day)

    plt.figure(figsize=(10,5))
    plt.title('Examples of boxplot',fontsize=20)
    plt.boxplot(boxes, labels = labels)
    plt.show()
