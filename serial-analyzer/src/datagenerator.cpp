#include "datagenerator.h"
#include "settings.h"

SerialSimulationDataGenerator::SerialSimulationDataGenerator() = default;

SerialSimulationDataGenerator::~SerialSimulationDataGenerator() = default;

void SerialSimulationDataGenerator::Initialize( U32 simulation_sample_rate, SerialAnalyzerSettings* settings )
{
    mSimulationSampleRateHz = simulation_sample_rate;
    mSettings = settings;

    mClockGenerator.Init( mSettings->mBitRate, simulation_sample_rate );
    mSerialSimulationData.SetChannel( mSettings->mInputChannel );
    mSerialSimulationData.SetSampleRate( simulation_sample_rate );

    mBitLow = BIT_LOW;
    mBitHigh = BIT_HIGH;

    mSerialSimulationData.SetInitialBitState( mBitHigh );
    mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod( 10.0 ) ); // insert 10 bit-periods of idle

    mValue = 0;

    mMpModeAddressMask = 0;
    mMpModeDataMask = 0;
    mNumBitsMask = 0;

    U32 num_bits = 8;
    for( U32 i = 0; i < num_bits; i++ )
    {
        mNumBitsMask <<= 1;
        mNumBitsMask |= 0x1;
    }

}

U32 SerialSimulationDataGenerator::GenerateSimulationData( U64 largest_sample_requested, U32 sample_rate,
                                                           SimulationChannelDescriptor** simulation_channels )
{
    U64 adjusted_largest_sample_requested =
        AnalyzerHelpers::AdjustSimulationTargetSample( largest_sample_requested, sample_rate, mSimulationSampleRateHz );

    while( mSerialSimulationData.GetCurrentSampleNumber() < adjusted_largest_sample_requested )
    {

            CreateSerialByte( mValue++ );

            mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod( 10.0 ) ); // insert 10 bit-periods of idle
        
    }

    *simulation_channels = &mSerialSimulationData;


    return 1; // we are retuning the size of the SimulationChannelDescriptor array.  In our case, the "array" is length 1.
}

void SerialSimulationDataGenerator::CreateSerialByte( U64 value )
{
    // assume we start high

    mSerialSimulationData.Transition();                                     // low-going edge for start bit
    mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod() ); // add start bit time

    U32 num_bits = 8;

    BitExtractor bit_extractor( value, AnalyzerEnums::LsbFirst , num_bits );

    for( U32 i = 0; i < num_bits; i++ )
    {
        mSerialSimulationData.TransitionIfNeeded( bit_extractor.GetNextBit() );
        mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod() );
    }


        if( AnalyzerHelpers::IsEven( AnalyzerHelpers::GetOnesCount( value ) ) == true )
            mSerialSimulationData.TransitionIfNeeded( mBitLow ); // we want to add a zero bit
        else
            mSerialSimulationData.TransitionIfNeeded( mBitHigh ); // we want to add a one bit

        mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod() );
    

    mSerialSimulationData.TransitionIfNeeded( mBitHigh ); // we need to end high

    // let's pad the end a bit for the stop bit:
    mSerialSimulationData.Advance( mClockGenerator.AdvanceByHalfPeriod( 2 ) );
}
