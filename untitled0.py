from docplex.mp.model import Model
from collections import defaultdict
#System after Disruption but right before the initialization of the restoration
class Res_System:
    def __init__(self, T, System1, t1):
        self.Adj = np.zeros([T, System1.NodeNum, System1.NodeNum])
        self.LinkCap = System1.LinkCap
        self.NodeCap = System1.NodeCap
        self.NodeNum = System1.NodeNum
        self.InitSystem = System1
        self.t1 = t1 #the beginning time of the whole restoration
        self.T = T
        
        self.Flow = np.zeros([T, System1.NodeNum, System1.NodeNum])
        self.Flow_Object = np.zeros([T, self.NodeNum, self.NodeNum], dtype = object)
        self.trN = np.zeros(self.NodeNum)
        self.trN_Object = np.zeros(self.NodeNum, dtype = object)
        self.tfN = np.zeros(self.NodeNum)
        self.tfN_Object = np.zeros(self.NodeNum, dtype = object)
        self.trL = np.zeros([self.NodeNum, self.NodeNum])
        self.trL_Object = np.zeros([self.NodeNum, self.NodeNum], dtype = object)
        self.tfL = np.zeros([self.NodeNum, self.NodeNum])
        self.tfL_Object = np.zeros([self.NodeNum, self.NodeNum], dtype = object)
        
        self.XN = np.zeros([T, System1.NodeNum])
        self.XN_Object = np.zeros([T, System1.NodeNum], dtype = object)
        self.XL = np.zeros([T, System1.NodeNum, System1.NodeNum])
        self.XL_Object = np.zeros([T, System1.NodeNum, System1.NodeNum], dtype = object)
        
        self.NodeOp = np.zeros([T, System1.NodeNum])
        self.NodeOp_Object = np.zeros([T, System1.NodeNum], dtype = object)
        self.LinkOp = np.zeros([T, System1.NodeNum, System1.NodeNum])
        self.LinkOp_Object = np.zeros([T, System1.NodeNum, System1.NodeNum], dtype = object)
        
        self.trN_dic = dict()
        self.tfN_dic = dict()
        self.trL_dic = dict()
        self.tfL_dic = dict()
        self.Flow_dic = dict()
        self.XN_dic = dict()
        self.XL_dic = dict()
    
    def InitUpdate(self, Disruption):#t1- the start time of the restoration
        if(self.t1 < len(self.InitSystem.Performance)):
            self.Adj[0, :, :] = self.InitSystem.TimeAdj[self.t1]
            self.Flow[0, :, :] = self.InitSystem.FlowAdj[self.t1]
        else:
            self.Adj[0, :, :] = self.InitSystem.TimeAdj[-1]
            self.Flow[0, :, :] = self.InitSystem.FlowAdj[-1]
    
        self.LinkOp[0, :, :] = self.Flow[0, :, :]/self.LinkCap
        for node in range(self.NodeNum):
            self.NodeOp[0, node] = self.Flow[0][:, node].sum()/self.NodeCap[node]
            
    def RepairRatio(self, beta):##Repair Speed: Capacity/Constant, quantifying how much capacity can we repair 
        self.NReRatio = self.NodeCap/beta
        self.LReRatio = self.LinkCap/beta
        
    def OptModelDefine(self, Name):
        self.mdl = Model(Name)
        
    def OpVarDefine(self):
        #tr, tf: integer Variables defining the beginning and finishing time of restoration for each link and node
        for node1 in range(self.NodeNum):
            exec("self.trN{} = self.mdl.integer_var(lb = self.t1, ub = self.T, name = 'trN{}')".format(node1, node1))
            exec("self.tfN{} = self.mdl.integer_var(lb = self.t1, ub = self.T, name = 'tfN{}')".format(node1, node1))
            
            self.trN_dic['trN{}'.format(node1)] = [eval('self.trN{}'.format(node1)), None]
            self.tfN_dic['tfN{}'.format(node1)] = [eval('self.tfN{}'.format(node1)), None]
            
            self.trN_Object[node1] = eval('self.trN{}'.format(node1))
            self.tfN_Object[node1] = eval('self.tfN{}'.format(node1))
            
            for node2 in range(self.NodeNum):
                exec("self.trL{}_{} = self.mdl.integer_var(lb = self.t1, ub = self.T, name = 'trL{}_{}')".format(node1, node2, node1, node2))
                exec("self.tfL{}_{} = self.mdl.integer_var(lb = self.t1, ub = self.T, name = 'tfL{}_{}')".format(node1, node2, node1, node2))
               
                self.trL_dic['trL{}_{}'.format(node1, node2)] = [eval('self.trL{}_{}'.format(node1, node2)), None]
                self.tfL_dic['tfL{}_{}'.format(node1, node2)] = [eval('self.tfL{}_{}'.format(node1, node2)), None]
    
                self.trL_Object[node1, node2] = eval('self.trL{}_{}'.format(node1, node2))
                self.tfL_Object[node1, node2] = eval('self.tfL{}_{}'.format(node1, node2))
        #XN, XL: Binary Variable determining whether the link and node is in the restoration or not
        #1 when current time step t in [tr, tf], 0 otherwise
        for t in range(T):
            for node1 in range(self.NodeNum):
                exec("self.XN{}_{} = self.mdl.binary_var(name = 'XN{}_{}')".format(t, node1, t, node1))
                
                self.XN_dic['XN{}_{}'.format(t, node1)] = [eval('self.XN{}_{}'.format(t, node1)), None]
                
                self.XN_Object[t, node1] = eval('self.XN{}_{}'.format(t, node1))
                for node2 in range(self.NodeNum):
                    exec("self.XL{}_{}_{} = self.mdl.binary_var(name = 'XL{}_{}_{}')".format(t, node1, node2, t, node1, node2))
                    
                    self.XL_dic['XL{}_{}_{}'.format(t, node1, node2)] = [eval('self.XL{}_{}_{}'.format(t, node1, node2)), None]
                    
                    self.XL_Object[t, node1, node2] = eval('self.XL{}_{}_{}'.format(t, node1, node2))
                    
        #f_tij: Continuous Variable determining the value of the flow
        for t in range(T):
            for node1 in range(self.NodeNum):
                for node2 in range(self.NodeNum):   
                    exec("self.f{}_{}_{} = self.mdl.continuous_var(lb = 0, name = 'f{}_{}_{}')".format(t, node1, node2, t, node1, node2))
                    
                    self.Flow_dic['f{}_{}_{}'.format(t, node1, node2)] = [eval('self.f{}_{}_{}'.format(t, node1, node2)), None]
                    
                    self.Flow_Object[t, node1, node2] = eval('self.f{}_{}_{}'.format(t, node1, node2))
        
    def OpCtDefine(self):
        #tf is no less than tr, f doesn't decrease along the time
        for node1 in range(self.NodeNum):
            self.mdl.add_constraint(self.trN_Object[node1] <= self.tfN_Object[node1])
            
            for node2 in range(self.NodeNum):
                self.mdl.add_constraint(self.trL_Object[node1, node2] <= self.tfL_Object[node1, node2])
                
                for t in range(self.T - 1):
                    self.mdl.add_constraint(self.Flow_Object[t, node1, node2] <= self.Flow_Object[t + 1, node1, node2])
        
        #The Restoration Binary Varibale XN, XL
        #1 when current time step t in [tr, tf], 0 otherwise
        for t in range(self.T):
            for node1 in range(self.NodeNum):
                self.mdl.add_if_then(t < self.trN_Object[node1], self.XN_Object[t, node1] = 0)
                self.mdl.add_if_then(t >= self.tfN_Object[node1], self.XN_Object[t, node1] = 0)
                self.mdl.add_constraint(self.mdl.sum(XN in self.XN_Object[:, node1]) = self.trN_Object[node1] - self.tfN_Object[node1])
        #The current operability
        
                
                
            
     

    
        
#T, The Whole Simulation Time; t1: The Beginning of the Restoration Time
T, t1 = 10, 3
#The speed of repairment, how much capaciity can it be restored per time unit
beta = 10
Shelby_County_Res = Res_System(T, Shelby_County, t1)
Shelby_County_Res.InitUpdate(Earth)
Shelby_County_Res.RepairRatio(beta)
Shelby_County_Res.OptModelDefine('Sc_op')
Shelby_County_Res.OpVarDefine()
Shelby_County_Res.OpCtDefine()



    


    
    
    
        
    
    
    