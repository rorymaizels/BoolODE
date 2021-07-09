__author__ = 'Jon Mallen'

import os
import sys
import shutil
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from umap import UMAP
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import itertools

# Define arguments
parser = argparse.ArgumentParser("Visualize the simulated single-cell gene expression data output by BoolODE.")
parser.add_argument('-f', '--pathToFiles', default='', type=str, help='Specify path to folder containing the '
                                                                      'ExpressionData.csv and PseudoTime.csv files '
                                                                      'generated by the BoolODE simulation, as well as '
                                                                      'the ClusterIds.csv present if the user '
                                                                      'specified at least 2 clusters in the '
                                                                      'simulation.')
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
parser.add_argument('-n', '--dataName', default='', nargs='*', help='Enter name of regulatory network.')

# Parse arguments and exit if proper files are not present
args = parser.parse_args()
path = args.pathToFiles
inFile = path + "/ExpressionData.csv"
if not os.path.exists(inFile):
    sys.exit('Error: No ExpressionData.csv file is present in the specified path to files.')
timeFile = path + "/PseudoTime.csv"
if not os.path.exists(timeFile):
    sys.exit('Error: No PseudoTime.csv file is present in the specified path to files.')
cluster_flag = args.clusterFile
clusterFile = args.pathToFiles + "/ClusterIds.csv"
if cluster_flag and not os.path.exists(clusterFile):
    sys.exit('Error: No ClusterIds.csv file is present in the specified path to files.')
pca_flag = args.pca is not None
tsne_flag = args.tsne is not None
umap_flag = args.umap is not None

# Do PCA, tSNE, UMAP
DF = pd.read_csv(inFile, sep=',', index_col=0)
Cells = DF.T.values
DRDF = pd.DataFrame(index=pd.Index(list(DF.columns)))


def dimensional_reduction(method, method_arg):

    # Check dimensions
    if len(method_arg) == 0:
        dim = 2
    elif len(method_arg) > 1:
        sys.exit('Error: Gave too many values for the number of dimensions. Please specify only a single number of '
                 'dimensions (2 or 3) for each dimensional reduction method.')
    else:
        dim = int(method_arg[0])
    if dim != 2 and dim != 3:
        sys.exit('Error: Specified an invalid number of dimensions. Only 2 and 3 are valid dimensions.')

    # Perform dimensional reduction
    embed = eval("%s(n_components=%s).fit_transform(Cells)" % (method, dim))
    for n in range(dim):
        DRDF['%s%d' % (method, n+1)] = embed[:, n]
    return dim


# Do PCA, t-SNE, UMAP
if pca_flag:
    pca_dim = dimensional_reduction('PCA', args.pca)
if tsne_flag:
    tsne_dim = dimensional_reduction('TSNE', args.tsne)
if umap_flag:
    umap_dim = dimensional_reduction('UMAP', args.umap)

# Color preparation

# Prepare time-dependent color scheme
#   To prepare the time-dependent color scheme,  the pseudo-time file is read for its maximum value, i.e the simulation
#   time. Then, the list of times corresponding to each cell is acquired as a list by splitting the title of each cell
#   into its sample number and time slice, and choosing only the time slice value. The time slice values can then be
#   scaled by the maximum value such that they are a value in [0,1], and can then be used to map each data point in the
#   dimensional reduction by time using a color map.

ptDF = pd.read_csv(timeFile, sep=',', index_col=0)
time_color_scale = max(ptDF["Time"])
time_colors = [int(h.split('_')[1]) / time_color_scale for h in DF.columns]
DRDF['Simulation Time'] = time_colors

# Prepare cluster-dependent color scheme
#   Just like the list of times for the time-dependent color scheme, the cluster values for each cell prepared from
#   k-means clustering are read for their maximum value. The maximum value is used to scale the list of cluster
#   assignments to values in [0,1], which can then be used to map each data point in the dimensional reduction by
#   cluster using a color map.

if cluster_flag:
    CF = pd.read_csv(clusterFile, sep=',', index_col=0)
    cluster_colors_raw = CF['cl'].tolist()
    cluster_color_scale = max(CF['cl'])
    cluster_colors = [y / cluster_color_scale for y in cluster_colors_raw]
else:
    cluster_colors = list(itertools.repeat(.5, len(DF.columns)))
DRDF['k-Means Clusters'] = cluster_colors

# Write dimensionality reduction data to text file
DRDF.to_csv('ExpressionData_dimred.csv', sep=",")
if os.path.exists(path + '/ExpressionData_dimred.csv'):
    os.remove(path + '/ExpressionData_dimred.csv')
shutil.move(os.path.abspath('ExpressionData_dimred.csv'), path)


def subplot_format(f, ax, plot_index, method, dim, map_title, color_map):
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
        ax[plot_index] = f.add_subplot(1, 2, plot_index+1, projection="3d")
        ax[plot_index].scatter3D(DRDF[labels_df.at[0, '1']], DRDF[labels_df.at[0, '2']], DRDF[labels_df.at[0, '2']],
                                 c=DRDF[map_title])
        ax[plot_index].set_zlabel(labels_df.at[1, '3'])
    else:
        ax[plot_index].scatter(DRDF[labels_df.at[0, '1']], DRDF[labels_df.at[0, '2']], c=DRDF[map_title])
    ax[plot_index].set_xlabel(labels_df.at[1, '1'])
    ax[plot_index].set_ylabel(labels_df.at[1, '2'])
    ax[plot_index].set_aspect('auto')
    ax[plot_index].set_title(map_title, fontsize=10)


def make_subplot(method, dim):
    if method == 'TSNE':
        method_name = 't-SNE'
    else:
        method_name = method
    plot_title = ' '.join(args.dataName) + ': Dimensional Reduction of Simulated Expression Data via %d-D %s' \
                 % (dim, method_name)
    f, ax = plt.subplots(1, 2, figsize=(10, 5))

    # Plot each cell in the dimensional reduction and map by simulation time using a color map.
    subplot_format(f, ax, 0, method, dim, 'Simulation Time', 'viridis')

    # Plot each cell in the dimensional reduction and map by cluster using a color map.
    subplot_format(f, ax, 1, method, dim, 'k-Means Clusters', 'Spectral')

    plt.suptitle(plot_title, fontsize=13)


# t-SNE plotting
if tsne_flag:
    make_subplot('TSNE', tsne_dim)
    plt.savefig(inFile.split('.csv')[0] + '_tSNE_%sd.png' % tsne_dim)

# PCA plotting
if pca_flag:
    make_subplot('PCA', pca_dim)
    plt.savefig(inFile.split('.csv')[0] + '_PCA_%sd.png' % pca_dim)

# UMAP plotting
if umap_flag:
    make_subplot('UMAP', umap_dim)
    plt.savefig(inFile.split('.csv')[0] + '_UMAP_%sd.png' % umap_dim)

plt.show()
