
#include "ll_analyzer.h"
#include "ll_settings.h"
#include <AnalyzerChannelData.h>
#include <AnalyzerResults.h>

ll_analyzer::ll_analyzer() : Analyzer2(), mSettings( new ll_settings() )
{
    SetAnalyzerSettings( mSettings.get() );
    UseFrameV2();
}

ll_analyzer::~ll_analyzer()
{
    KillThread();
}

void ll_analyzer::SetupResults()
{
    // Unlike the worker thread, this function is called from the GUI thread
    // we need to reset the Results object here because it is exposed for direct access by the GUI, and it can't be deleted from the
    // WorkerThread

    mResults.reset( new ll_results( this, mSettings.get() ) );
    SetAnalyzerResults( mResults.get() );
    mResults->AddChannelBubblesWillAppearOn( mSettings->mInputChannel );
}

void ll_analyzer::WorkerThread()
{

    mBits = GetAnalyzerChannelData( mSettings->mInputChannel );
    // Get rate in samples per second
    float rate = GetSampleRate() / 1000000;

    // Loop forever (Starting HIGH)
    for( ;; )
    {
        // Get this bit
        U64 this_bit = mBits->GetSampleNumber();
        U64 next_bit = mBits->GetSampleOfNextEdge();
        U64 bit_width = next_bit - this_bit;
        U8 bit;

        // Record Bit State
        bit = mBits->GetBitState() == BIT_HIGH ? 1 : 0; 

        mResults->AddMarker(
            this_bit,
            bit ? AnalyzerResults::UpArrow : AnalyzerResults::DownArrow, 
            mSettings->mInputChannel);
        Frame frame;
        frame.mStartingSampleInclusive = static_cast<S64>(this_bit);
        frame.mEndingSampleInclusive = static_cast<S64>(next_bit);
        frame.mData1 = (U64) bit;
        mResults->AddFrame( frame );

        FrameV2 frameV2;
        frameV2.AddByte( "data", bit );
        frameV2.AddDouble("length", bit_width);
        frameV2.AddDouble("nanoseconds", round((bit_width*1000)/ rate));
        mResults->AddFrameV2(frameV2, "BIT", this_bit, next_bit);

        // Report this result
        mResults->CommitResults();
        ReportProgress( mBits->GetSampleNumber() );
        CheckIfThreadShouldExit();

        // Move to the next bit
        mBits->AdvanceToNextEdge();
    }
}


bool ll_analyzer::NeedsRerun()
{
    return false;
}

U32 ll_analyzer::GenerateSimulationData( U64 minimum_sample_index, U32 device_sample_rate,
                                          SimulationChannelDescriptor** simulation_channels )
{
    return 0;
}


U32 ll_analyzer::GetMinimumSampleRateHz()
{
    return 200000 * 4;
}

const char* ll_analyzer::GetAnalyzerName() const
{
    return ANALYZER_NAME;
}

const char* GetAnalyzerName()
{
    return ANALYZER_NAME;
}

Analyzer* CreateAnalyzer()
{
    return new ll_analyzer();
}

void DestroyAnalyzer( Analyzer* analyzer )
{
    delete analyzer;
}
