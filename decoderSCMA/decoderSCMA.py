
import config
import codebook64 as CODEBOOK
import encoderConfig
import math
import numpy as np

class _DecoderHelper():

    def getMessage(self, k, j,codewords):
        eta_k = config.factorGraph[k];
        sigma_x = 0;
        for i, vNode in enumerate(eta_k):
            if vNode == 1:
                #print("codewords",CODEBOOK.getCodeword(i+1, codewords[i])[k]);
                sigma_x += CODEBOOK.getCodeword(i+1, codewords[i])[k];
        dividend = config.resourceLayer[k]-sigma_x;
        return np.exp(-(dividend*dividend.conjugate())/(config.sigma**2)).real

    def productSequencev_f(self, k, j, codewords):
        eta_k = config.factorGraph[k];
        pi_Ev_f = 1;
        for i, vNode in enumerate(eta_k):
            if vNode == 1 and i != j:
                pi_Ev_f *= config.Ev_f[k, i, codewords[i].astype(int)];
        return pi_Ev_f;

    def getEf_v(self, k, j, cw):
        eta_k = config.factorGraph[k];
        if eta_k[j] != 1:
            return 0;
        update = 0;
        codewords = np.zeros(shape=(CODEBOOK.userNum(),1),dtype=np.integer);
        index_A = None;
        index_B = None;

        # initiate codewords
        for i, vNode in enumerate(eta_k):
            if vNode == 1:
                if i == j:
                    codewords[i] = cw;
                else:
                    if(index_A is None):
                        index_A = i;
                    else:
                        index_B = i;
                    codewords[i] = 0;
        while codewords[index_A] < 4:
            while codewords[index_B] < 4:
                message = self.getMessage(k, j,codewords);
                product = self.productSequencev_f(k,j,codewords);
                update += message*product;
                codewords[index_B] += 1;
            codewords[index_B] = 0;
            codewords[index_A] += 1;

        #difference = np.absolute(codewords[index_A]-encoderConfig.userSymbols[index_A]);
        #difference += np.absolute(codewords[index_B]-encoderConfig.userSymbols[index_B]);
        #difference += np.absolute(codewords[j]-encoderConfig.userSymbols[j]);
        #if difference > 7 or difference < 2:

        #print("codewords-userSymbols",np.absolute(codewords[j]-encoderConfig.userSymbols[j]));
        #print("update",update);
        #print(encoderConfig.userSymbols[j],cw,np.abs(update))
        if update.any():
            return update[0];

    def getCodeword(k,j,codewords):
        eta_k = config.factorGraph[k];
        indexOfCW = 0;
        for i, vNode in enumerate(eta_k):
            if vNode == 1:
                if i == j:
                    return codewords[indexOfCW];
                indexOfCW += 1;
    def productSequencef_v(self,k,j,cw):
        epsilon_j = config.factorGraph[:,j];
        pi_Ef_v = 1;
        for i, fNode in enumerate(epsilon_j):
            if fNode == 1 and i != k:
                pi_Ef_v *= config.Ef_v[i,j,cw];
        return pi_Ef_v;
    def All_productSequencef_v(self,j,cw):
        epsilon_j = config.factorGraph[:,j];
        pi_Ef_v = 1;
        for i, fNode in enumerate(epsilon_j):
            if fNode == 1:
                pi_Ef_v *= config.Ef_v[i,j,cw];
        return pi_Ef_v;
    #Normalization

    def magnitude(self,v):
        return math.sqrt(sum(np.absolute(v[i])**2 for i in range(len(v))))

    def add(u, v):
        return [ u[i]+v[i] for i in range(len(u)) ]

    def sub(u, v):
        return [ u[i]-v[i] for i in range(len(u)) ]

    def dot(u, v):
        return sum(u[i]*v[i] for i in range(len(u)))

    def normalize(self,v):
        vmag = self.magnitude(v);
        return v/vmag;

    def getEv_f(self,k, j):
        if config.factorGraph[:,j][k] != 1:
            return 0;
        normalizedProduct = np.zeros( shape = (CODEBOOK.codeWordSize()),dtype=np.complex);
        cw = 0;
        for indexOfCW in range(CODEBOOK.codeWordSize()):
            normalizedProduct[indexOfCW] = self.productSequencef_v(k,j,cw);
            cw += 1;
        cw = 0;
        normalizedProduct = self.normalize(normalizedProduct);
        #print("********after normalization********")
        #print(k,j,cw,normalizedProduct);
        return normalizedProduct;

DECODERHELPER = _DecoderHelper();
def messagePassing():
    # update message from Function Node to Variable Node
    #print("********Info from vNode to fNode********")

    for k in range(config.factorGraph.shape[0]):
        for j in range(config.factorGraph.shape[1]):
            for index in range(config.numCodeWords):
                config.Ef_v[k,j,index] = DECODERHELPER.getEf_v(k,j,index);
                #print(k,j,index,config.Ef_v[k,j,index]);
    # update message from V Node to F Node
    #print("********Info from fNode to vNode********")
    for j in range(config.factorGraph.shape[1]):
        for k in range(config.factorGraph.shape[0]):
            config.Ev_f[k,j,:] = DECODERHELPER.getEv_f(k,j);
            #print("userSymbols",encoderConfig.userSymbols[j]);
            #print("final",k,j,config.Ev_f[k,j,:]);
def iterativeMPA(iteration):
    for i in range(iteration):
        messagePassing();
def estimateSymbol():
    for j in range(config.factorGraph.shape[1]):
        probX_j = np.zeros( shape = (CODEBOOK.codeWordSize()),dtype=np.complex);
        for indexOfCW in range(CODEBOOK.codeWordSize()):
            probX_j[indexOfCW] = DECODERHELPER.All_productSequencef_v(j,indexOfCW);
        config.EstimatedSymbols[j] = np.argmax(probX_j);
