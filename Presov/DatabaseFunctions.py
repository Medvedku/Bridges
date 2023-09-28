import sys
import numpy as np
import pickle
from pymongo import MongoClient
from datetime import datetime
import time
import matplotlib.pyplot as plt
from matplotlib import gridspec as grd
from matplotlib import dates as plt_dates

from argparse import FileType
import smtplib
import imghdr
from email.message import EmailMessage

def win(a:str = "ok", tajm=0.1):
    """
    Dummy function, takes no argument and returns print statement.
    Its purpose is for debugging.
    
    PARAMETERS:
    a :             printed statement
    tajm :          sleep time at the end of function
    """
    print(a)
    time.sleep(tajm)


def anisodiff1D(sig, num_iter: int, delta_t=1/6, kappa=100, option=1, dx=1, verbose=False):
    """
    anisodiff1D perfoms conventional anisotropic diffusion (Perona & Malik)
    upon 1D signals. A 1D network structure of 2 neighboring nodes 
    is considered for diffusion conduction.
  
    PARAMETERS:
    sig :           input vector
    num_iter :      number of iterations
    delta_t :       integrstion constant (0 <= delta_t <= 1/3)
                    usually, due to numerical stability this porameter
                    is set to its maximum value
    kappa :         gradient modulus threshold that controls condution
    option :        conduction coeficient functions proposed by Perona & Malik
                    1 - privileges hight-contrast edges over low-contrast ones
                    2 - privileges wide regions over smaller ones
    dx :            time (sampling period) 
    verbose :       prints computational info if True

    RETURNS:
    diff_sig:       (diffused) signal with the largest scale-space parameter
    """

    # Double precision of input vector.
    if type(sig) == list:
        sig = np.double(np.array(sig))
    elif str(type(sig)) == "<class 'numpy.ndarray'>":
        sig = np.double(sig)
    else:
        sys.exit("Data type of argument \"option\" should be \"list\" or \"numpy.ndarray\", not " + str(type(sig)))
    
    # Number of elements in list
    n = len(sig)

    # PDE (partial differential equation) initial condition. 
    diff_sig = sig

    # Anisotropic diffusion.
    for t in range(num_iter):
        sig = np.append(sig, sig[-2])
        sig = np.insert(sig, 0, sig[1])
        # Differences
        nablaW = [(-sig[i+1]+sig[i]) for i in range(n)]
        nablaE = [(+sig[i+2]-sig[i+1]) for i in range(n)]
        nablaW = np.array(nablaW)
        nablaE = np.array(nablaE)

        # Diffusion function.
        if option == 1:
            cW = np.exp(-(nablaW/kappa)**2)
            cE = np.exp(-(nablaE/kappa)**2)
        elif option == 2:
            cW = 1/(1 + (nablaW/kappa)**2)
            cE = 1/(1 + (nablaE/kappa)**2)
        elif option == 3:
            cW = 1/(1 + (nablaW**2)*kappa)
            cE = 1/(1 + (nablaE**2)*kappa)
        else:
            sys.exit("Value of an argument \"option\" should be \'1\' or \'2\', not " + str(option))

        # Discrete PDE solution. Explicit scheme
        # diff_sig = diff_sig + delta_t * \
        #     (1/(dx**2)*cW*nablaW + 1/(dx**2)*cE*nablaE)

        # Discrete PDE solution. Semiimplicit scheme
        B = 1 + delta_t / dx**2 * (cW + cE)
        C = - delta_t / dx**2 * cE
        A = - delta_t / dx**2 * cW

        B[0] = 1; B[-1] = 1
        C[0] = 0; A[-1] = 0

        # right side of equations (vector original values)
        D = sig
        diff_sig = ThomasAlgo(A, B, C, D)
              
        
        # Info
        if verbose:
            print("Iteration ", t, diff_sig)
            print(nablaW, nablaE)
            print(cW, cE)
        
        sig = diff_sig

    return diff_sig

def ThomasAlgo(A, B, C, D, verbose=False):
    """
    Solves three diagonal sparse matrix system.

    PARAMETERS:
    A :             lower diagonal
    B :             diagonal
    C :             upper diagonal
    D :             right side of system of equations

    OPTIONAL :
    verbose :       prints computational info if True

    RETURNS:
    X :             solution vector
    """
    A = list_to_nparray_check(A, "A")
    B = list_to_nparray_check(B, "B")
    C = list_to_nparray_check(C, "C")
    D = list_to_nparray_check(D, "D")

    n = len(A)

    # Create new coefficients

    for i in range(n-1):
        w = A[i+1] / B[i]
        B[i+1] = B[i+1] - w * C[i]
        D[i+1] = D[i+1] - w * D[i]

    X = np.zeros( (1, n) )[0]
    # Back substitution
    X[-1] = D[-1] / B[-1]
    
    for i in range(n-2, -1, -1):
        X[i] = (D[i] - C[i] * X[i+1]) / B[i]

    return X


def list_to_nparray_check(X, name="X"):
    if type(X) == list:
        X = np.array(X)
    elif str(type(X)) == "<class 'numpy.ndarray'>":
        pass
    else:
        sys.exit(
            "Data type of argument \"" + name + "\" should be \"list\" or \"numpy.ndarray\", not " + str(type(X)))
    return X


def pickley(database:str, collection:str, t_from=0, t_end=3e9, file_name:str="data.pickle", path:str='Stojan/pickles/', verbose=False) -> list:
    """
    Pickles XERXES database from chosen time up to chosen time.
    
    PARAMETERS:
    databese :          chose xerxes database
    collection :        chose xerxes collection
    t_from :            start time
    t_end :             end time
    path :              path to file
    file_name :         name of the file

    OPTIONAL :
    verbose :           prints computational info if True

    RETURNS:
    pickle              returns pickled database
    """

    mongo_URI = "mongodb+srv://node:prokopcakovamama@xerxes.57jmr.mongodb.net/alfa?retryWrites=true&w=majority"
    cluster = MongoClient(mongo_URI)

    db = cluster[database]
    col = db[collection]
    l_ = []
    for i in col.find({ "$and": [{"time.epoch": {"$gt": t_from}}, {"time.epoch": {"$lt": t_end}}]}):
        l_.append(i)
    path_name = path + file_name
    with open(path_name, 'wb') as f:
        pickle.dump(np.array(l_), f)
    if verbose:
        print(file_name + " pickled")


def unpickley(path:str='pickles/',file_name:str='data.pickle', verbose=False):
    """
    Unpickles XERXES database from chosen pickled file.
    
    PARAMETERS:
    path :              folder in which is pickled file located
    collection :        pickled file
    path :              path to file
    file_name :         name of the file

    OPTIONAL :
    verbose :           prints computational info if True

    RETURNS:
    data_list           returns unpickled database
    """

    full_path = path+file_name   
    with open(full_path, 'rb') as f:
        data_list = pickle.load(f)
    if verbose:
        print("Data " + file_name + " unpickled")
    return data_list

def get_epoch(year:int, month:int, day:int, hour:int, minute:int, second:int) -> float:
    """
    Creates epoch from provided year, month, day, hour, minute and second.
    
    PARAMETERS:
    year :              wanted year
    month :             wanted month
    day :               wanted day
    hour :              wanted hour
    minute :            wanted minute
    second :            wanted second

    OPTIONAL:
    verbose :           prints computational info if True

    RETURNS:
    pickle              returns pickled database from

    e.g.:               get_epoch(2022, 6, "2", 19.0, 13, 0)
    """

    if any([(type(i) is not int) for i in [year, month, day, hour, minute]]):
        try:
            year=int(year); month=int(month); day=int(day); 
            hour=int(hour); minute=int(minute); second=int(second);
        except:
            print("Invalid input")
            return

    epoch = datetime(year, month, day, hour, minute, second).timestamp()
    return epoch