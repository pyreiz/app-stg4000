# -*- coding: utf-8 -*-
from functools import lru_cache
from time import sleep
from typing import List
from stg._wrapper.dll import (
    System,
    CURRENT,
    VOLTAGE,
    available,
    select,
    DeviceInfo,
    DownloadInterface,
    bitmap,
)


class STG4000:
    def sleep(self, duration: float):
        sleep(duration)

    def __init__(self, serial: int = None):
        if serial is None:
            info = available()[0]
        else:
            info = select(serial)
        print("Selecting {0:s}:SN {1:s}".format(info.DeviceName, info.SerialNumber))
        self._info = info
        self.interface = lambda: DownloadInterface(info)
        self.diagonalize_triggermap()

    @property
    def name(self):
        "returns the model name, i.e. STG4002/4/8"
        return self._info.DeviceName

    @property
    def version(self):
        "Returns the current hardware and software version"
        soft, hard = self._version
        return "Hardware - {0} : Software - Version: {1}".format(
            hard.replace("Rev.", "Revision"), soft
        )

    @property
    def _version(self):
        with self.interface() as interface:
            _, soft, hard = interface.GetStgVersionInfo("", "")
        return soft, hard

    @property
    def serial_number(self):
        "Returns the serial number of the device"
        return int(self._info.SerialNumber)

    @property
    def manufacturer(self):
        "Returns the name of the manufacturer"
        return self._info.Manufacturer

    def __repr__(self):
        return f"{str(self)} at {hex(id(self))}"

    def __str__(self):
        return self._info.ToString()

    def set_current_mode(self, channel_index: List[int] = []):
        """set a single or all channels to current mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to current mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.        
        """
        if channel_index == []:
            with self.interface() as interface:
                interface.SetCurrentMode()
        else:
            with self.interface() as interface:
                for chan in channel_index:
                    interface.SetCurrentMode(System.UInt32(chan))

    def set_voltage_mode(self, channel_index: List[int] = []):
        """set a single or all channels to voltage mode
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes an integer of the target channel.
            Indexing starts at 0.
        
        """
        if channel_index == []:
            with self.interface() as interface:
                interface.SetVoltageMode()
        else:
            with self.interface() as interface:
                for chan in channel_index:
                    interface.SetVoltageMode(System.UInt32(chan))

    @property
    def current_resolution_in_uA(self):
        with self.interface() as interface:
            out = interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / 1000
        return out

    @property
    def current_resolution_in_mA(self):
        with self.interface() as interface:
            out = interface.GetCurrentResolutionInNanoAmp(System.UInt32(0)) / (
                1000 * 1000
            )
        return out

    @property
    def current_range_in_mA(self):
        with self.interface() as interface:
            out = interface.GetCurrentRangeInNanoAmp(System.UInt32(0)) / (1000 * 1000)
        return out

    @property
    def current_range_in_uA(self):
        with self.interface() as interface:
            out = interface.GetCurrentRangeInNanoAmp(System.UInt32(0)) / (1000)
        return out

    @property
    def voltage_resolution_in_uV(self):
        with self.interface() as interface:
            out = interface.GetVoltageResolutionInMicroVolt(System.UInt32(0))
        return out

    @property
    def voltage_range_in_mV(self):
        with self.interface() as interface:
            out = interface.GetVoltageRangeInMicroVolt(System.UInt32(0)) / (1000)
        return out

    @property
    def time_resolution_in_us(self):
        return 20

    @property
    def time_resolution_in_ms(self):
        return 0.02

    @property
    def DAC_resolution(self):
        with self.interface() as interface:
            out = interface.GetDACResolution()
        return out

    @property
    def channel_count(self):
        "returns the number of stimulation channels"
        with self.interface() as interface:
            out = interface.GetNumberOfAnalogChannels()
        return out

    @property
    def trigin_count(self):
        "returns the number of  trigger inputs"
        with self.interface() as interface:
            out = interface.GetNumberOfTriggerInputs()
        return out

    def stop_stimulation(self, triggerIndex: List[int] = []):
        """stops all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap. By default, all triggers are mapped to channels following diagonal identity, i.e. trigger 0 maps to channel 0. This is done during initialization of the STG4000 object. Use :meth:`~STG4000.diagonalize_triggermap` to repeat this normalization.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """

        if triggerIndex == []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStop(System.UInt32(bitmap(triggerIndex)))

    def start_stimulation(self, triggerIndex: List[int] = []):
        """starts all trigger inputs or a selection based on a list 
        
        Triggers are mapped to channels according to the channelmap. By default, all triggers are mapped to channels following diagonal identity, i.e. trigger 0 maps to channel 0. This is done during initialization of the STG4000 object. Use :meth:`~STG4000.diagonalize_triggermap` to repeat this normalization.
        
        args
        ----
        channel_index:list
            defaults to all, which sets all channels to voltage mode
            otherwise, takes a list of integers of the targets, 
            e.g. [0,1]
            Indexing starts at 0.
        
        """

        if triggerIndex is []:
            triggerIndex = [c for c in range(self.channel_count)]
        with self.interface() as interface:
            interface.SendStart(System.UInt32(bitmap(triggerIndex)))

    def diagonalize_triggermap(self):
        """Normalize the channelmap to a diagonal
                
        Triggers are mapped to channels according to the channelmap. This is 
        done at the lower level with interface.SetupTrigger. 
        
        Use this function to normalize the mapping of trigger to channel to a diagonal identity, i.e. trigger 0 maps to channel 0,  so on.

            +----------+---+---+---+---+---+---+---+---+
            | Trigger  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            +----------+---+---+---+---+---+---+---+---+
            | Channel  | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
            +----------+---+---+---+---+---+---+---+---+
        
        """
        channelmap = []
        syncoutmap = []
        repeat = []
        for chan_idx in range(0, self.channel_count):
            repeat.append(1)  # every trigger only once
            syncoutmap.append(1 << chan_idx)  # diagonal triggerout
            channelmap.append(1 << chan_idx)  # diagonal triggerin
        with self.interface() as interface:
            interface.SetupTrigger(0, channelmap, syncoutmap, repeat)

    def download(
        self,
        channel_index: int = 0,
        amplitudes_in_mA: List[float,] = [0],
        durations_in_ms: List[float,] = [0],
    ):

        """Download a stimulation signal 
        
        The signal is compressed to amplitudes and their respective durations 
        
        args
        ----
        
        channel_index:int
            The index of the channel for which to download the signal. Indexing
            starts at 0
        amplitude:List[float,]
            a list of amplitudes in mA/mV delivered for the corresponding duration 
        duration:List[float,]
            a list of durations in ms determing how long each corresponding 
            amplitude is delivered

        .. example::
            
             mcs.download(channel_index = 0,
                          amplitude = [1, -1, 0],
                          duration = [.1, .1, .488])
             sets the first channel to a biphasic pulse with 100µs duration
             each and an amplitude of 1000µA, i.e 1mA.
        
        notes:
           The signal is downloaded with  interface.PrepareAndSendData, 
           therefore previous data sent to that channel is erased first.
        """

        amplitudes = [int(a * 1000_000) for a in amplitudes_in_mA]
        durations = [int(s * 1000) for s in durations_in_ms]
        self._download([channel_index], amplitudes, durations, "current")

    def _download(
        self,
        channel_index: List[int] = [0],
        amplitudes: List[int] = [0],
        durations: list = [20],
        mode="current",
    ):

        if len(amplitudes) != len(durations):
            raise ValueError("Every amplitude needs a duration and vice versa!")
        amplitudes = [System.Int32(a) for a in amplitudes]
        durations = [System.UInt64(d) for d in durations]

        if mode == "current":
            self.set_current_mode(channel_index)
            with self.interface() as interface:
                for chan in channel_index:
                    interface.PrepareAndSendData(chan, amplitudes, durations, CURRENT)
        elif mode == "voltage":
            self.set_voltage_mode(channel_index)
            with self.interface() as interface:
                for chan in channel_index:
                    interface.PrepareAndSendData(chan, amplitudes, durations, VOLTAGE)

