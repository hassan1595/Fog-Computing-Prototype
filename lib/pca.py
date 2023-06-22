import numpy as np
import scipy.linalg as la


class PCA():


    def __init__(self, Xtrain):
        """
        initialises the PCA class

        :Xtrain: training data as numpy array with shape (nxd)
        """ 


        # help variables
        n = len(Xtrain)
        d = len(Xtrain[0])

        # calculate center
        self.C = np.mean(Xtrain, axis = 0)

        # caluclating covariance matrix 
        cov_mat = np.zeros((d, d))
        for x_i in Xtrain:
            cov_mat+= np.dot(np.reshape((x_i - self.C), (1,-1)).T , np.reshape((x_i - self.C), (1, -1)))
        cov_mat = 1/(n-1) * cov_mat

        # caluclate eigenvalues and eigenvectors and sort them according to eigenvalues descendingly
        e_vals, e_vecs = la.eig(cov_mat)
        idxs = e_vals.argsort()[::-1]

        # use calculated indices to sort eigenvectors and values
        self.U = e_vecs[:,idxs] 
        self.D = e_vals[idxs] 

    def project(self, Xtest, m):
        """
        project centered points using first m principal directions computed before.

        :Xtest:  test data as numpy array with shape (nxd)
        :return: projected data in shape (nxm)
        """ 

        w_mat = self.U[:,:m]
        Z = np.dot(w_mat.T, (Xtest - self.C).T).T

        return Z

    def denoise(self, Xtest, m):

        """
        caluclate projected component of every data point and project it on the principal direction and undo centering.

        :Xtest:  test data as numpy array with shape (nxd)
        :return: denoised data in original shape (nxd)
        """ 

        projected_pts = self.project(Xtest, m).T
        projected_vecs = self.U[:,:m]

        Y = np.dot(projected_vecs, projected_pts).T + self.C
        return Y



def gammaidx(X, k):
    """
    calculates the gama index which is the average distance between one points and its k nearest neighbors. used to identify ourliers.

    :X: data set in shape (nxd)
    :k: number of neighbors
    :return: gamma index (int)
    """ 

    y = np.zeros(len(X))

    for idx, x_i in enumerate(X):

        dist= la.norm((X - x_i), axis = 1)
        dist_k = np.sort(dist)[1:k+1]
        y[idx] = np.mean(dist_k)

    return y