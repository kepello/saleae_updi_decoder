
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

bool ll_analyzer::Valid( BitState bit, U64 Width = 0)
{
    U64 this_width = channel->GetSampleOfNextEdge() - channel->GetSampleNumber();
    if (Width == 0) 
        Width = RateWidth;
    // Check Bit
    if (channel->GetBitState() != bit) {
        Identify(channel->GetSampleNumber(), "WRONG_BIT", FLAG_WRONG_BIT);
        return false;
    } else if ( this_width < ( Width * .5 ) ) {
        Identify(channel->GetSampleNumber(), "NARROW", FLAG_NARROW);
        return false;
    } else if ( this_width > ( Width * 1.5 ) ) {
        Identify(channel->GetSampleNumber(), "WIDE", FLAG_WIDE );
        return false;
    } else {
        return true;
    }

}


void ll_analyzer::Identify(U64 start, const char* note, FrameFlags flag, int value) {
    if (value != -1) {
        Frame frame;
        frame.mStartingSampleInclusive = static_cast<S64>(start);
        frame.mEndingSampleInclusive = static_cast<S64>(channel->GetSampleOfNextEdge());
        frame.mData1 = (U64)value;
        frame.mFlags = flag;
        mResults->AddFrame( frame );
    }

    FrameV2 frameV2;
    if (value != -1)
        frameV2.AddByte( "data", value );
    mResults->AddFrameV2( frameV2, note, channel->GetSampleNumber(), channel->GetSampleOfNextEdge());
}

void ll_analyzer::WorkerThread()
{

    U64 sync_start = 0;
    U64 this_width = 0;
    U8 bit_count = 0;
    U64 rate_width = 0;
    channel = GetAnalyzerChannelData( mSettings->mInputChannel );

    // We should start at high state (IDLE) at the beginning of a capture
    if (channel->GetBitState() == BIT_LOW) {
        Identify(channel->GetSampleNumber(), "START", FLAG_START);
        channel->AdvanceToNextEdge();
    }

    // We don't know rate yet, until we get our first SYNC
    updi_state state = updi_state::SYNC;

    for( ;; )
    {
        if (bit_count == 0) {
            // LOW is start of a SYNC
            // 0 1234567 8  9
            // S 0123456 7P SS
            // L HLHLHLH LL HH
            if (( channel->GetBitState() == BIT_LOW)) {
                sync_start = channel->GetSampleNumber();
                // First bit we get a presumptive width
                RateWidth = channel->GetSampleOfNextEdge() - channel->GetSampleNumber();
                //Identify("BIT0", FLAG_NONE, RateWidth);
                bit_count++;
            } else {
                Identify(channel->GetSampleNumber(), "IDLE", FLAG_IDLE);
                bit_count = 0;
            }
        }
        else if( bit_count < 8 )
        {
            // Check the widths of subsequent single wide-bits
            if (!Valid((bit_count & 0x01) ? BIT_HIGH : BIT_LOW)) {
                bit_count = 0;
                sync_start = 0;
            } else { 
                //Identify("BIT<8", FLAG_NONE, RateWidth);
                bit_count++;
            }
        }
        else if (bit_count == 8) 
        {
            if (!Valid(BIT_LOW, RateWidth * 2)) 
            {
                bit_count = 0;
                sync_start = 0;
            } else {
                bit_count++;
                Identify(channel->GetSampleNumber(), "BIT8-9", FLAG_NONE, RateWidth);
            }
        } 
        else
        {
            if (!Valid(BIT_HIGH, RateWidth*2))
            {
                    bit_count = 0;
                    sync_start = 0;
            } else {
                Identify(sync_start, "SYNC", FLAG_SYNC);
                sync_start = 0;
                bit_count = 0;
            }
        }

        mResults->CommitResults();
        ReportProgress( channel->GetSampleNumber());
        channel->AdvanceToNextEdge();
        CheckIfThreadShouldExit();
        
    }


    // Get rate in samples per second
    //float rate = GetSampleRate() / 1000000;

    // Loop forever (Starting HIGH)
    for( ;; )
    {
        // Get this bit
        U64 this_bit = channel->GetSampleNumber();
        U64 next_bit = channel->GetSampleOfNextEdge();
        U64 bit_width = next_bit - this_bit;
        U8 bit;

        // Record Bit State
        bit = channel->GetBitState() == BIT_HIGH ? 1 : 0; 

    //Identify("BIT", bit);
        // mResults->AddMarker(
        //     this_bit,
        //     bit ? AnalyzerResults::UpArrow : AnalyzerResults::DownArrow, 
        //     mSettings->mInputChannel);
        // Frame frame;
        // frame.mStartingSampleInclusive = static_cast<S64>(this_bit);
        // frame.mEndingSampleInclusive = static_cast<S64>(next_bit);
        // frame.mData1 = (U64) bit;
        // mResults->AddFrame( frame );

        // FrameV2 frameV2;
        // frameV2.AddByte( "data", bit );
        // frameV2.AddDouble("length", bit_width);
        // frameV2.AddDouble("nanoseconds", round((bit_width*1000)/ rate));
        // mResults->AddFrameV2(frameV2, "BIT", this_bit, next_bit);

        // Report this result
        mResults->CommitResults();
        ReportProgress( channel->GetSampleNumber() );
        CheckIfThreadShouldExit();

        // Move to the next bit
        channel->AdvanceToNextEdge();
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
