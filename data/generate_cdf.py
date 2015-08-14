import matplotlib.pyplot as plt
import matplotlib
import sys
import numpy as np

def readData(path,scale=1.0,min=0.0, max=30.0):
    f = open(path)
    data = []
    for line in f:
        val = float(line.strip())
        if val > max or val < min:
            print str(val)
        else:
            data.append(val*scale)
        
    f.close()
    return sorted(data)


def drawThreeDelayCDF(data_chicago,data_ec2,data_local,data_chicago2,data_ec22,data_local2,xlim=0,xmax=0,ylabel="CDF RTT",xlabel="Time (ms)"):
    font = {'family' : 'normal',\
        'weight' : 'bold',\
        'size'   : 22}
    matplotlib.rc('font', **font)
    params = {'legend.fontsize': 20, 'axes.labelsize':25}
    plt.rcParams.update(params)
    fig = plt.figure(1)
    ax1 = plt.subplot(121) 
    [i.set_linewidth(6) for i in ax1.spines.itervalues()]
    #fig.suptitle("test",fontsize=15)
    #plt.legend([plot1,plot2,plot3], ["Chicago HoneyFarm", 'EC2 HoneyFarm',"Local HoneyFarm"],bbox_to_anchor=(0.31,1))
    data_chicago = np.sort(data_chicago) 
    data_ec2 = np.sort(data_ec2) 
    data_local = np.sort(data_local) 
    yvals1=np.arange(len(data_chicago))/float(len(data_chicago))
    eighty_index = int(0.8*len(data_chicago))
    print "I eighty percent for chicago: %f "%data_chicago[eighty_index]
    eighty_index = int(0.8*len(data_ec2))
    print "I eighty percent for ec2: %f "%data_ec2[eighty_index]
    eighty_index = int(0.8*len(data_local))
    print "I eighty percent for local: %f "%data_local[eighty_index]

    yvals2=np.arange(len(data_ec2))/float(len(data_ec2))
    yvals3=np.arange(len(data_local))/float(len(data_local))
    plt.xscale('log')
    if xlim != 0 and xmax != 0:
        plt.xlim(xlim,xmax)
    plot1, = plt.plot(data_chicago, yvals1, 'b',linewidth=6.0)
    plot2, = plt.plot(data_ec2, yvals2,'r',linewidth=6.0)
    plot3, = plt.plot(data_local, yvals3,'k', linewidth=6.0)
    plt.ylabel("CDF")
    yticks = np.arange(0, 1.1, 0.2)
    plt.yticks(yticks)
    plt.xlabel("Time (ms)")
    plt.legend([plot1,plot2,plot3], ["Chicago", 'EC2',"Local"],bbox_to_anchor=(1.05,1.12),ncol=3,loc=9,frameon=False)
    
    #figure 2
    #fig = plt.figure(2)
    ax2 = plt.subplot(122) 
    [i.set_linewidth(6) for i in ax2.spines.itervalues()]
    #fig.suptitle("test",fontsize=15)
    data_chicago = np.sort(data_chicago2) 
    data_ec2 = np.sort(data_ec22) 
    data_local = np.sort(data_local2) 
    eighty_index = int(0.8*len(data_chicago))
    print "NI eighty percent for chicago: %f "%data_chicago[eighty_index]
    eighty_index = int(0.8*len(data_ec2))
    print "NI eighty percent for ec2: %f "%data_ec2[eighty_index]
    eighty_index = int(0.8*len(data_local))
    print "NI eighty percent for local: %f "%data_local[eighty_index]

    yvals1=np.arange(len(data_chicago))/float(len(data_chicago))
    yvals2=np.arange(len(data_ec2))/float(len(data_ec2))
    yvals3=np.arange(len(data_local))/float(len(data_local))
    plt.xscale('log')
    if xlim != 0 and xmax != 0:
        plt.xlim(xlim,xmax)
    plot1, = plt.plot(data_chicago, yvals1, 'b',linewidth=6.0)
    plot2, = plt.plot(data_ec2, yvals2,'r',linewidth=6.0)
    plot3, = plt.plot(data_local, yvals3,'k', linewidth=6.0)
    
    #plt.title('Initial RTT')
    #plt.ylabel("Non-initial RTT CDF")
    plt.yticks(yticks)
    plt.xlabel(xlabel)
    plt.show()


def drawCDF2(data1):
    font = {'family' : 'normal',\
        'weight' : 'bold',\
        'size'   : 22}
    matplotlib.rc('font', **font)
    params = {'legend.fontsize': 20, 'axes.labelsize':25}
    plt.rcParams.update(params)
    fig = plt.figure(1)
    ax1 = plt.subplot(111) 
    [i.set_linewidth(6) for i in ax1.spines.itervalues()]
    
    plt.xlim(0,31)
    data1 = np.sort(data1) 
    #data2 = np.sort(data2) 
    #data3 = np.sort(data3) 
    yvals1=np.arange(len(data1))/float(len(data1))
    eighty_index = int(0.8 * len(data1))
    nighty_index = int(0.9 * len(data1))
    #yvals2=np.arange(len(data2))/float(len(data2))
    #yvals3=np.arange(len(data3))/float(len(data3))
    #plt.xlim(0.05,3)
    #plt.xscale('log')
    plot1, = plt.plot(data1, yvals1,linewidth=6.0)
    plot2, = plt.plot(data2, yvals2,'r--')
    #plot3, = plt.plot(data3, yvals3,'y--')
    plt.ylabel("CDF")
    #plt.yticks(yticks)
    plt.xlabel("Loading time (s)")
    #plt.legend([plot1,plot2,plot3], ["Chicago HoneyFarm", 'EC2 HoneyFarm',"Local HoneyFarm"],bbox_to_anchor=(0.8,0.25))
    print "Eightyth %f "%data1[eighty_index]
    print "Nightyth %f "%data1[nighty_index]

    plt.show()



def main():
   
    data = readData(sys.argv[1],max=300)
    drawCDF2(data)
    #drawThreeDelayCDF(data1,data2,data3,data11,data22,data33)
    
    #drawCDF2(data)


if __name__=="__main__":
    main()
