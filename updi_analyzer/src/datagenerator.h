#pragma once

#include <AnalyzerHelpers.h>

class updi_settings;

class SerialSimulationDataGenerator
{
  public:
    SerialSimulationDataGenerator();
    ~SerialSimulationDataGenerator();

    void Initialize( U32 simulation_sample_rate, updi_settings* settings );
    U32 GenerateSimulationData( U64 newest_sample_requested, U32 sample_rate, SimulationChannelDescriptor** simulation_channels );

  protected:
    updi_settings* mSettings;
    U32 mSimulationSampleRateHz;
    BitState mBitLow;
    BitState mBitHigh;
    U64 mValue;

    U64 mMpModeAddressMask;
    U64 mMpModeDataMask;
    U64 mNumBitsMask;

  protected: // Serial specific
    void CreateSerialByte( U64 value );
    ClockGenerator mClockGenerator;
    SimulationChannelDescriptor mSerialSimulationData; // if we had more than one channel to simulate, they would need to be in an array
};
