__author__ = 'Jon Mallen'


# Visualize simulated expression data produced from a BoolODE simulation through the dimensional reduction technique
# of the user's choice. Expression data is visualized through pseudo-time, k-means clustering, and cells called to be
# in steady states by the counterpart script genSS.py if that option is specified.


import os
import sys
import shutil
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from umap import UMAP
import matplotlib.pyplot as plt
import pandas as pd
import argparse
from itertools import repeat
from functools import partial
from binarize_data import binarize_data


# Common method for dimensional reduction
def dimensional_reduction(method, method_arg, dimred_df):
    if len(method_arg) == 0:
        dim = 2
    elif len(method_arg) > 1:
        sys.exit('Error: Gave too many values for the number of dimensions. Please specify only a single number of '
                 'dimensions (2 or 3) for each dimensional reduction method.')
    else:
        dim = int(method_arg[0])
    if dim != 2 and dim != 3:
        sys.exit('Error: Specified an invalid number of dimensions. Only 2 and 3 are valid dimensions.')
    embed = eval("%s(n_components=%s).fit_transform(Cells)" % (method, dim))
    for n in range(dim):
        dimred_df['%s%d' % (method, n+1)] = embed[:, n]
    return dim


def subplot_format(f, ax, num_plots, plot_index, dataframe, method, dim, map_title, color_map, axis_limits):
    plt.rcParams['image.cmap'] = color_map
    labels_df = pd.DataFrame()
    for m in range(1, dim + 1):
        label_list = ['%s%d' % (method, m)]
        if method == 'TSNE':
            label_list.append('t-SNE %d' % m)
        else:
            label_list.append('%s %d' % (method, m))
        labels_df[str(m)] = label_list
    if dim == 3:
        ax[plot_index].set_axis_off()
        ax[plot_index] = f.add_subplot(1, num_plots, plot_index+1, projection="3d")
        ax[plot_index].scatter3D(dataframe[labels_df.at[0, '1']], dataframe[labels_df.at[0, '2']],
                                 dataframe[labels_df.at[0, '2']], c=dataframe[map_title])
        ax[plot_index].set_zlabel(labels_df.at[1, '3'])
        z_range = list(ax[plot_index].get_zlim())
    else:
        ax[plot_index].scatter(dataframe[labels_df.at[0, '1']], dataframe[labels_df.at[0, '2']],
                               c=dataframe[map_title])
    ax[plot_index].set_xlabel(labels_df.at[1, '1'], fontsize=14)
    ax[plot_index].set_ylabel(labels_df.at[1, '2'], fontsize=14)
    ax[plot_index].set_aspect('auto')
    if plot_index == 2:
        plot_title = 'Cells in Steady-States'
    else:
        plot_title = map_title
    ax[plot_index].set_title(plot_title, fontsize=12)
    x_range = list(ax[plot_index].get_xlim())
    y_range = list(ax[plot_index].get_ylim())
    if plot_index == 0:
        if dim == 3:
            plot_ranges = [x_range, y_range, z_range]
        else:
            plot_ranges = [x_range, y_range]
        return plot_ranges
    if plot_index == 2:
        ax[plot_index].set_xlim(axis_limits[0])
        ax[plot_index].set_ylim(axis_limits[1])
        if dim == 3:
            ax[plot_index].set_zlim(axis_limits[2])


def make_subplot(method, dim, data_label, show_ss_flag, dimred_df, dimred_df_ss_only):
    if method == 'TSNE':
        method_name = 't-SNE'
    else:
        method_name = method
    plot_title = ' '.join(data_label) + ': Dimensional Reduction of Simulated Expression Data via %d-D %s' \
                 % (dim, method_name)
    if show_ss_flag:
        num_plots = 3
        fig_width = 15
    else:
        num_plots = 2
        fig_width = 10
    f, ax = plt.subplots(1, num_plots, figsize=(fig_width, 5))
    partial_subplot_format = partial(subplot_format, f=f, ax=ax, num_plots=num_plots, method=method, dim=dim)
    # plot_ranges = subplot_format(f, ax, num_plots, 0, dimred_df, method, dim, 'Simulation Time', 'viridis', None)
    plot_ranges = partial_subplot_format(plot_index=0, dataframe=dimred_df, map_title='Simulation Time',
                                         color_map='viridis', axis_limits=None)
    # Plot each cell in the dimensional reduction and map by simulation time using a color map.
    partial_subplot_format(plot_index=0, dataframe=dimred_df, map_title='Simulation Time',
                           color_map='viridis', axis_limits=plot_ranges)
    # Plot each cell in the dimensional reduction and map by cluster using a color map.
    partial_subplot_format(plot_index=1, dataframe=dimred_df, map_title='k-Means Clusters',
                           color_map='Spectral', axis_limits=plot_ranges)
    # Plot only the cells corresponding to steady-states using a color map.
    if show_ss_flag:
        partial_subplot_format(plot_index=2, dataframe=dimred_df_ss_only, map_title='Steady State Groups',
                               color_map='jet', axis_limits=plot_ranges)
    plt.suptitle(plot_title, fontsize=15)
    for ax in ax.flat:
        ax.label_outer()


if __name__ == '__main__':

    # Define arguments
    parser = argparse.ArgumentParser("Visualize the simulated single-cell RNA-seq data output by BoolODE.")
    parser.add_argument('-f', '--pathToFiles', default='', type=str, help='Specify path to folder containing the '
                                                                          'ExpressionData.csv and PseudoTime.csv files '
                                                                          'generated by the BoolODE simulation, as '
                                                                          'well as the ClusterIds.csv if it is '
                                                                          'present.')
    parser.add_argument('-p', '--pca', nargs='*', help='Use PCA for visualizing the data. '
                                                       'Specify the number of dimensions (2 or 3) as argument. '
                                                       'Default is 2.')
    parser.add_argument('-t', '--tsne', nargs='*', help='Use t-SNE for visualizing the data. '
                                                        'Specify the number of dimensions (2 or 3) as argument. '
                                                        'Default is 2.')
    parser.add_argument('-u', '--umap', nargs='*', help='Use UMAP for visualizing the data. '
                                                        'Specify the number of dimensions (2 or 3) as argument. '
                                                        'Default is 2.')
    parser.add_argument('-c', '--clusterFile', action='store_true', default=False,
                        help='Use the cluster file ClusterIds.csv to assign clusters if the user specified at least 2 '
                             'clusters in the simulation.')
    parser.add_argument('-s', '--ssFile', nargs=1, type=str, help='Specify path to folder containing the '
                                                                  'steady_states.tsv file to be used for labeling '
                                                                  'which cells in the expression data for this network '
                                                                  'are steady states called by genSS.py.')
    parser.add_argument('-n', '--dataName', default='Network', nargs='*', help='Enter name of the regulatory network.')

    # Path to expression data, pseudo-time, cluster file, and steady states file
    args = parser.parse_args()
    path = args.pathToFiles
    inFile = path + "/ExpressionData.csv"
    if not os.path.exists(inFile):
        sys.exit('Error: No ExpressionData.csv file is present in the specified path to files.')
    timeFile = path + "/PseudoTime.csv"
    if not os.path.exists(timeFile):
        sys.exit('Error: No PseudoTime.csv file is present in the specified path to files.')
    cluster_flag = args.clusterFile
    clusterFile = path + "/ClusterIds.csv"
    if cluster_flag and not os.path.exists(clusterFile):
        sys.exit('Error: No ClusterIds.csv file is present in the specified path to files.')
    data_name = args.dataName
    ss_flag = args.ssFile is not None
    if ss_flag:
        ssFile = "".join(args.ssFile) + "/steady_states.tsv"
    else:
        ssFile = ""
    if ss_flag and not os.path.exists(ssFile):
        sys.exit('Error: No steady_states.tsv file is present in the specified path to files.')
    pca_flag = args.pca is not None
    tsne_flag = args.tsne is not None
    umap_flag = args.umap is not None

    # Read the expression data
    DF = pd.read_csv(inFile, sep=',', index_col=0)
    Cells = DF.T.values
    cell_list = list(DF.columns)
    DRDF = pd.DataFrame(index=pd.Index(cell_list))
    binDF = binarize_data(DF)

    # Do PCA, t-SNE, UMAP
    partial_dimensionality_reduction = partial(dimensional_reduction, dimred_df=DRDF)
    if pca_flag:
        pca_dim = partial_dimensionality_reduction(method='PCA', method_arg=args.pca)
    if tsne_flag:
        tsne_dim = partial_dimensionality_reduction(method='TSNE', method_arg=args.tsne)
    if umap_flag:
        umap_dim = partial_dimensionality_reduction(method='UMAP', method_arg=args.umap)

    # Prepare time-dependent color scheme
    #   To prepare the time-dependent color scheme,  the pseudo-time file is read for its maximum value, i.e the
    #   simulation time. Then, the list of times corresponding to each cell is acquired as a list by splitting the
    #   title of each cell into its sample number and time slice, and choosing only the time slice value. The time
    #   slice values can then be scaled by the maximum value such that they are a value in [0,1], and can then be
    #   used to map each data point in the dimensional reduction by time using a color map.

    ptDF = pd.read_csv(timeFile, sep=',', index_col=0)
    time_color_scale = max(ptDF["Time"])
    time_colors = [int(h.split('_')[1]) / time_color_scale for h in DF.columns]
    DRDF['Simulation Time'] = time_colors

    # Prepare cluster-dependent color scheme
    #   Just like the list of times for the time-dependent color scheme, the cluster values for each cell prepared from
    #   k-means clustering are read for their maximum value. The maximum value is used to scale the list of cluster
    #   assignments to values in [0,1], which can then be used to map each data point in the dimensional reduction by
    #   cluster using a color map.

    single_color = list(repeat(.5, len(DF.columns)))
    if cluster_flag:
        CF = pd.read_csv(clusterFile, sep=',', index_col=0)
        cluster_colors_raw = CF['cl'].tolist()
        cluster_color_scale = max(CF['cl'])
        cluster_colors = [y / cluster_color_scale for y in cluster_colors_raw]
    else:
        cluster_colors = single_color
    DRDF['k-Means Clusters'] = cluster_colors

    # Write dimensionality reduction data to text file
    DRDF.to_csv('ExpressionData_dimred.csv', sep=",")
    if os.path.exists(path + '/ExpressionData_dimred.csv'):
        os.remove(path + '/ExpressionData_dimred.csv')
    shutil.move(os.path.abspath('ExpressionData_dimred.csv'), path)

    # Isolate steady states from DRDF
    #   Just like for the time-dependent color scheme and cluster color scheme, the cells corresponding to steady
    #   states are grouped to their respective steady state, and assigned to a list scaled by the number of steady
    #   states with values in [0,1]. This can then be used to map each data point in the dimensional reduction by
    #   steady state using a color map.

    if ss_flag:
        ss_df = pd.read_csv(ssFile, sep="\t", index_col=0)
        if list(ss_df.columns) != list(DF.index):
            sys.exit('Error: The steady_states.tsv file does not contain the same gene names as the simulated '
                     'expression data of the network. The file may correspond to a different network.')
        ss_list = ss_df.values.tolist()
        num_steady_states = len(ss_list)
        DRDF_ss_only = pd.DataFrame(columns=DRDF.columns)
        ss_colors = []
        for i in range(len(cell_list)):
            for j in range(num_steady_states):
                if ss_list[j] == list(binDF[cell_list[i]]):
                    ss_colors.append(j / num_steady_states)
                    DRDF_ss_only.loc[len(DRDF_ss_only.index)] = DRDF.iloc[i]
        DRDF_ss_only["Steady State Groups"] = ss_colors

    # t-SNE plotting
    partial_make_subplot = partial(make_subplot, data_label=data_name, show_ss_flag=ss_flag, dimred_df=DRDF,
                                   dimred_df_ss_only=DRDF_ss_only)
    if tsne_flag:
        partial_make_subplot(method='TSNE', dim=tsne_dim)
        plt.savefig(inFile.split('.csv')[0] + '_tSNE_%sd.png' % tsne_dim)
        # PCA plotting
    if pca_flag:
        partial_make_subplot(method='PCA', dim=pca_dim)
        plt.savefig(inFile.split('.csv')[0] + '_PCA_%sd.png' % pca_dim)
        # UMAP plotting
    if umap_flag:
        partial_make_subplot(method='UMAP', dim=umap_dim)
        plt.savefig(inFile.split('.csv')[0] + '_UMAP_%sd.png' % umap_dim)
    plt.show()
