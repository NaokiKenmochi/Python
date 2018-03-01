from RT1DataBrowser import DataBrowser
from matplotlib import gridspec
import sys
sys.path.append('/Users/kemmochi/PycharmProjects/ControlCosmoZ')

import numpy as np
import pywt
import read_wvf
import czdec
import scipy.signal as sig
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib as mpl
#mpl.use('Qt4Agg')


class STFT_RT1(DataBrowser):
    def __init__(self, date, shotNo, LOCALorPPL):
        """

        :param date:
        :param shotNo:
        """
        super().__init__(date, shotNo, LOCALorPPL)
        self.date = date
        self.shotnum = shotNo
        self.LOCALorPPL = LOCALorPPL

    def load_ep01(self, LOCALorPPL):
        if LOCALorPPL == "PPL":
            dm_ep01 = read_wvf.DataManager("exp_ep01", 0, self.date)
            data_ep01 = dm_ep01.fetch_raw_data(self.shotnum)
            print("Load ep01 from PPL")

        else:
            data = np.load("IF_%s_%d.npz" % (self.date, self.shotnum))
            data_ep02_SX = data["data_ep02_SX"]
            filename = "GP1_20171110_107_IF1IF2FAST.txt"
            IF_FAST = np.loadtxt(filename, delimiter=",")
            print("Load SX from local")

        return data_ep01

    def load_IF_FAST(self, LOCALorPPL):
        if LOCALorPPL == "PPL":
            dm_ep02_SX = read_wvf.DataManager("exp_ep02", "SX", self.date)
            data_ep02_SX = dm_ep02_SX.fetch_raw_data(self.shotnum)
            print("Load SX from PPL")

        else:
            data = np.load("IF_%s_%d.npz" % (self.date, self.shotnum))
            data_ep02_SX = data["data_ep02_SX"]
            filename = "GP1_20171110_107_IF1IF2FAST.txt"
            IF_FAST = np.loadtxt(filename, delimiter=",")
            print("Load SX from local")

        return data_ep02_SX

    def load_MP_FAST(self, LOCALorPPL):
        if LOCALorPPL == "PPL":
            dm_ep02_MP = read_wvf.DataManager("exp_ep02", "MP", self.date)
            data_ep02_MP = dm_ep02_MP.fetch_raw_data(self.shotnum)
            print("Load MP from PPL")

        else:
            data = np.load("MP123_%s_%d.npz" % (self.date, self.shotnum))
            data_ep02_MP = data["data_ep02_MP"]
            print("Load MP from local")

        return data_ep02_MP

    def load_SX_FAST(self, LOCALorPPL):
        if LOCALorPPL == "PPL":
            dm_ep02_SX = read_wvf.DataManager("exp_ep02", "SX", self.date)
            data_ep02_SX = dm_ep02_SX.fetch_raw_data(self.shotnum)
            print("Load SX from PPL")

        else:
            data = np.load("SX123_%s_%d.npz" % (self.date, self.shotnum))
            data_ep02_MP = data["data_ep02_SX"]
            print("Load SX from local")

        return data_ep02_SX

    def load_SX_CosmoZ(self, LOCALorPPL):
        if LOCALorPPL == "PPL":
            data = czdec.CosmoZ_DataBrowser(filepath= '/Volumes/share/Cosmo_Z_xray/', filename="", date=self.date, shotnum=self.shotnum)
            data_SX = data.read_cosmoz()
            print("Load SX from PPL")

        else:
            #data = np.load("/Users/kemmochi/PycharmProjects/ControlCosmoZ/SX_%s_%d.npz" % (self.date, self.shotnum))
            data = np.load("data/19.npz")
            data_SX = data['energy']
            time_SX = data['time']
            print("Load SX from local")

        return data_SX, time_SX

    def cwt(self):
        # TODO: 時間がかかりすぎる　要確認
        #IF_FAST = self.load_IF_FAST("PPL")
        #MP_FAST = self.load_MP_FAST("PPL")
        #y = MP_FAST[1, :]
        #x = MP_FAST[0, :]
        num_IF = 1
        y = IF_FAST[num_IF, ::1000]
        x = np.linspace(0, 2, 2000)
        #N = 1e-3*np.abs(1/(x[1]-x[2]))
        N=4000
        wfreq = np.linspace(1,N, 4000)
        #coef = sig.cwt(y, sig.ricker, wfreq)
        #coef, freqs=pywt.cwt(y, wfreq, 'cmor')
        coef, freqs=pywt.cwt(y, wfreq, 'mexh')

        MAXFREQ = 1e0
        #plt.xlim(0, 1.0)
        #plt.contourf(t, f, np.abs(Zxx), 200, norm=LogNorm())# vmax=1e-7)
        plt.ylabel("CWT Frequency of IF%d [Hz]" % (num_IF))
        plt.xlabel("Time [sec]")
        #plt.ylim([0, MAXFREQ])
        #plt.xlim([0.8, 2.2])
        #ax3.contourf(x, 200/wfreq, coef, 200)
        plt.contourf(x,N*freqs, np.sqrt(np.real(coef)**2+np.imag(coef)**2), 100, vmax=5.0)
        #ax3.contourf(x, 200/wfreq, np.sqrt(np.real(coef)**2+np.imag(coef)**2), 200, vmax=0.4)
        #plt.colorbar()
        plt.title("Date: %s, Shot No.: %d" % (self.date, self.shotnum), loc='right', fontsize=20, fontname="Times New Roman")
        plt.show()

    def moving_average(self, x, N):
        # Take a moving average along axis=1 with window width N.
        x = np.pad(x, ((0, 0), (N, 0)), mode='constant')
        cumsum = np.cumsum(x, axis=1)
        return (cumsum[:, N:] - cumsum[:, :-N]) / N

    def cross_spectrum(self):
        data_ep01 = self.load_ep01("PPL")
        data_ep01 = self.adj_gain(data_ep01)
        data_ep01 = self.calib_IF(data_ep01)
        IF = data_ep01[9:12:2, :].T
        N = np.abs(1/(data_ep01[0, 1]-data_ep01[0, 2]))
        sampling_time = 1/N

        #IF_FAST = self.load_IF_FAST("PPL")
        #IF = IF_FAST[1:3, :].T
        #sampling_time = 1e-6
        #f, t, Pxx = sig.spectrogram(IF, axis=0, fs=1/sampling_time, window='hamming', nperseg=128, noverlap=64, mode='complex')
        #f, t, Pxx = sig.spectrogram(IF, axis=0, fs=1/sampling_time, window='hamming', nperseg=2**15, noverlap=512, mode='complex')
        f, t, Pxx = sig.spectrogram(IF, axis=0, fs=1/sampling_time, window='hamming', nperseg=2**9, noverlap=16, mode='complex')
        #Pxx_run = self.moving_average(Pxx[:, 0] * np.conj(Pxx[:, 1]), 8)
        Pxx_run = self.moving_average(Pxx[:, 0] * np.conj(Pxx[:, 1]), 2)

        DPhase = 180/np.pi*np.arctan2(Pxx_run.imag, Pxx_run.real)

        plt.pcolormesh(t, f, np.log(np.abs(Pxx_run)))
        #plt.pcolormesh(t, f, DPhase)
        plt.xlim(0.5, 2.5)
        #plt.clim(-16, -13)
        plt.clim(-28, -25)
        plt.ylim(0, 2000)
        plt.colorbar()
        plt.xlabel('Time [sec]')
        plt.ylabel('Frequency [Hz]')
        plt.show()

    def stft(self, IForMPorSX="IF", num_ch=1):

        time_offset_stft = 0.0
        if(IForMPorSX=="IF"):
            data_ep01 = self.load_ep01("PPL")
            data_ep01 = self.adj_gain(data_ep01)
            data_ep01 = self.calib_IF(data_ep01)

            y = data_ep01[10:13, :]
            x = data_ep01[0, :]
            filename = "STFT_IF_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 1e-5
            coef_vmax = 0.8
            NPERSEG = 2**9
            time_offset = 0.0

        if(IForMPorSX=="POL"):
            """
            390nm, 730nm, 710nm, 450nmの順で格納
            390nm, 450nmの比を用いて電子密度を計算
            730nm, 710nmの比を用いて電子温度を計算
            """
            data_ep01 = self.load_ep01("PPL")
            data_ep01 = self.adj_gain(data_ep01)

            y_buf1 = np.array([data_ep01[13, :]])
            y_buf2 = np.array(data_ep01[25:28, :])
            y = np.r_[y_buf1, y_buf2]
            x = data_ep01[0, :]
            filename = "STFT_POL_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 3e-3
            coef_vmax = 0.8
            NPERSEG = 2**9
            time_offset = 0.0

        if(IForMPorSX=="POL_RATIO"):
            """
            390nm, 450nmの比を用いて電子密度を計算
            730nm, 710nmの比を用いて電子温度を計算
            """
            data_ep01 = self.load_ep01("PPL")
            data_ep01 = self.adj_gain(data_ep01)

            y_Te = np.array([(data_ep01[27, :]+1.0)/(data_ep01[13, :]+1.0)])
            y_ne = np.array([(data_ep01[25, :]+1.0)/(data_ep01[26, :]+1.0)])
            y = np.r_[y_Te, y_ne]
            x = data_ep01[0, :]
            filename = "STFT_POL_RATIO_woffset_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 1e-6
            coef_vmax = 1.0e2
            NPERSEG = 2**8
            time_offset = 0.0

        if(IForMPorSX=="IF_FAST"):
            IF_FAST = self.load_IF_FAST("PPL")
            y = IF_FAST[1:, :]
            x = np.linspace(0, 2, 2000000)
            filename = "STFT_IF_FAST_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 5e-7
            coef_vmax = 0.8
            NPERSEG = 2**15
            time_offset = 0.75
            time_offset_stft = 0.75

        if(IForMPorSX=="MP"):
            MP_FAST = self.load_MP_FAST("PPL")
            y = MP_FAST[1:, :]
            x = MP_FAST[0, :]
            filename = "STFT_MP_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 1e-7
            coef_vmax = 0.8
            NPERSEG = 2**14
            #NPERSEG = 1024
            time_offset = 1.25
            time_offset_stft = 0.25
            #plt.plot(x, MP_FAST[1, :]+1, label="MP1")
            #plt.plot(x, MP_FAST[2, :], label="MP2")
            #plt.plot(x, MP_FAST[3, :]-1, label="MP3")
            #plt.legend()
            #plt.show()

        if(IForMPorSX=="SX"):
            data_SX, time_SX = self.load_SX_CosmoZ(self.LOCALorPPL)
            y = data_SX[:, 4]
            x = data_SX[:, 0]
            time_SX_10M = np.linspace(0, 2, 2e7)
            data_SX_10M = np.zeros(2e7)
            data_SX_10M[[i for i in time_SX*1e7]] = data_SX
            y = data_SX_10M
            x = time_SX_10M
            time_offset_stft = 1.00
            time_offset = 1.25
            #plt.plot(x, y)
            #plt.show()
            filename = "STFT_SX4_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 1e-7
            coef_vmax = 0.8

        if(IForMPorSX=="REF"):
            SX_FAST = self.load_SX_FAST("PPL")
            y = SX_FAST[3:, :]
            x = SX_FAST[0, :]
            filename = "STFT_REF_%s_%d" % (self.date, self.shotnum)
            vmin = 0.0
            vmax = 5e-7
            coef_vmax = 0.8
            NPERSEG = 2**14
            time_offset_stft = 0.75
            time_offset = 1.25
            #plt.plot(x, SX_FAST[3, :]+1, label="REF_COS")
            #plt.plot(x, SX_FAST[4, :], label="REF_SIN")
            #plt.plot(SX_FAST[3, ::10000], SX_FAST[4, ::10000])
            #plt.legend()
            #plt.show()


        N = np.abs(1/(x[1]-x[2]))

        for i in range(num_ch):

            #f, t, Zxx =sig.spectrogram(y[i, :], fs=N, window='hamming', nperseg=NPERSEG, mode='complex')
            f, t, Zxx =sig.spectrogram(y[i, :], fs=N, window='hamming', nperseg=NPERSEG)
            #f, t, Zxx =sig.stft(y[i, :], fs=N, window='hamming', nperseg=NPERSEG)
            if(i == 0):
                #Zxx_3D = np.zeros((np.shape(Zxx)[0], np.shape(Zxx)[1], num_ch), dtype=complex)
                Zxx_3D = np.zeros((np.shape(Zxx)[0], np.shape(Zxx)[1], num_ch))
            Zxx_3D[:, :, i] = Zxx[:, :]

        return f, t, Zxx_3D, filename, vmax, coef_vmax,  vmin, time_offset, time_offset_stft, x, y

    def plot_stft(self, IForMPorSX="IF", num_ch=4):
        f, t, Zxx_3D, filename, vmax, coef_vmax, vmin, time_offset, time_offset_stft, x, y = self.stft(IForMPorSX=IForMPorSX, num_ch=num_ch)

        #vmaxを求める際の時間(t)，周波数(f)の範囲とそのindexを取得
        t_st = 1.2
        t_ed = 1.4
        f_st = 550
        f_ed = 650
        idx_tst = np.abs(np.asarray(t - t_st)).argmin()
        idx_ted = np.abs(np.asarray(t - t_ed)).argmin()
        idx_fst = np.abs(np.asarray(f - f_st)).argmin()
        idx_fed = np.abs(np.asarray(f - f_ed)).argmin()

        plt.figure(figsize=(16, 5))
        gs = gridspec.GridSpec(4, num_ch)
        gs.update(hspace=0.4, wspace=0.3)
        for i in range(num_ch):
            ax0 = plt.subplot(gs[0:3, i])
            vmax_in_range = np.max(np.abs(Zxx_3D[idx_fst:idx_fed, idx_tst:idx_ted, i])) * coef_vmax
            plt.pcolormesh(t + time_offset_stft, f, np.abs(Zxx_3D[:, :, i]), vmin=vmin, vmax=vmax_in_range)
            sfmt=matplotlib.ticker.ScalarFormatter(useMathText=True)
            cbar = plt.colorbar(format=sfmt)
            cbar.ax.tick_params(labelsize=12)
            cbar.formatter.set_powerlimits((0, 0))
            cbar.update_ticks()
            ax0.set_xlabel("Time [sec]")
            ax0.set_ylabel("Frequency of %s%d [Hz]" % (IForMPorSX, i+1))
            ax0.set_xlim(0.5, 2.5)
            ax0.set_ylim([0, 2000])
            if(i==num_ch-1):
                plt.title("%s" % (filename), loc='right', fontsize=20, fontname="Times New Roman")

            ax1 = plt.subplot(gs[3, i])
            ax1.plot(x+time_offset, y[i, :])
            ax1.set_xlabel("Time [sec]")
            ax1.set_xlim(0.5, 3.0)
        plt.show()
        #filepath = "figure/"
        #plt.savefig(filepath + filename)

def make_stft_profile(date):
    r_pol = np.array([379, 432, 484, 535, 583, 630, 689, 745, 820])
    num_shots = np.array([80, 68, 69, 70, 71, 72, 73, 74, 75])      #For 23Dec2017
    #num_shots = np.array([87, 54, 89, 91, 93, 95, 97, 99, 101])    #For 23Feb2018

    for i in range(9):
        stft = STFT_RT1(date=date, shotNo=num_shots[i], LOCALorPPL="PPL")
        #f, t, Zxx_3D,_,_,_,_,_,_,_ = stft.stft(IForMPorSX="POL", num_ch=4)
        f, t, Zxx_3D,_,_,_,_,_,_,_ = stft.stft(IForMPorSX="POL", num_ch=4)
        if(i == 0):
            #Zxx_4D = np.zeros((np.shape(Zxx_3D)[0], np.shape(Zxx_3D)[1], np.shape(Zxx_3D)[2], r_pol.__len__()), dtype=complex)
            Zxx_4D = np.zeros((np.shape(Zxx_3D)[0], np.shape(Zxx_3D)[1], np.shape(Zxx_3D)[2], r_pol.__len__()))
        Zxx_4D[:, :, :, i] = Zxx_3D

    filename = 'Pol_woffset_stft_%s_%dto%d.npz' % (date, num_shots[0], num_shots[-1])
    np.savez_compressed(filename, r_pol=r_pol, f=f, t=t, Zxx_4D=Zxx_4D)

if __name__ == "__main__":
    for i in range(109, 110):
        stft = STFT_RT1(date="20171110", shotNo=i, LOCALorPPL="PPL")
        stft.plot_stft(IForMPorSX="IF", num_ch=3)
    #stft = STFT_RT1(date="20171110", shotNo=100, LOCALorPPL="PPL")
    #stft.plot_stft(IForMPorSX="POL", num_ch=4)
    #make_stft_profile(date="20171223")
    #stft.cwt()
    #stft.cross_spectrum()