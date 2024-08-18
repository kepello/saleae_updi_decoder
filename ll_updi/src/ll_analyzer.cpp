
#include "ll_analyzer.h"
#include "ll_settings.h"
#include <AnalyzerChannelData.h>
#include <AnalyzerResults.h>
#include <sstream>

ll_analyzer::ll_analyzer() : Analyzer2(), mSettings( new ll_settings() )
{
    SetAnalyzerSettings( mSettings.get() );
    ByteCount = 0;
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

bool ll_analyzer::Valid( BitState bit, U64 Width = 0 )
{
    U64 this_width = channel->GetSampleOfNextEdge() - channel->GetSampleNumber();
    if( Width == 0 )
        Width = bit_rate;
    // Check Bit
    if( channel->GetBitState() != bit )
    {
        Identify( "WRONG_BIT", FLAG_WRONG_BIT, -1 );
        return false;
    }
    else if( this_width < ( Width * .75 ) )
    {
        Identify( "NARROW", FLAG_NARROW, -1 );
        return false;
    }
    else if( this_width > ( Width * 2.5 ) )
    {
        if( channel->GetBitState() == BIT_HIGH )
            Identify( "IDLE", FLAG_IDLE, 0xFF );
        else
            Identify( "BREAK", FLAG_BREAK, 0x00 );
        return false;
    }
    else
    {
        return true;
    }
}

void ll_analyzer::Identify( U64 start, U64 end, const char* note, FrameFlags flag, int value )
{
    float baud;
    std::stringstream ss;

    // Add display on top of bit stream
    Frame frame;
    frame.mStartingSampleInclusive = static_cast<S64>( start );
    frame.mEndingSampleInclusive = static_cast<S64>( end );
    frame.mData1 = ( U64 )value;
    frame.mFlags = flag;
    mResults->AddFrame( frame );

    // Add table data
    FrameV2 frameV2;
    frameV2.AddByte( "count", ++ByteCount );

    if( flag == FrameFlags::FLAG_SYNC )
    {
        // Add Baud Rate
        baud = ( this->GetSampleRate() / frame.mData1 );
        ss << "(Baud Rate: " << baud << ")";


        // Add data for SYNC
        frameV2.AddByte( "data", 0x55 );
    }
    else
    {
        // Add data value if there is one
        if( value != -1 )
        {
            frameV2.AddByte( "data", value );
        }
    }
    
    mResults->AddFrameV2( frameV2, note, start, end );
}


void ll_analyzer::Identify( const char* note, FrameFlags flag, int value )
{
    Identify( channel->GetSampleNumber(), channel->GetSampleOfNextEdge(), note, flag, value );
}

void ll_analyzer::Identify( U64 start_time, const char* note, FrameFlags flag, int value )
{
    Identify( start_time, channel->GetSampleNumber() + ( bit_rate / 2 ), note, flag, value );
}


// We are not yet synchronized to our bitrate.  Return:
//    true:  We are still unsynced
//    false: We are now synced
bool ll_analyzer::unsynced()
{
    static U8 sync_bit_count = 0;
    static U64 sync_start = 0;

    if( sync_bit_count == 0 )
    {
        // LOW is start of a SYNC
        // 0 1234567 8  9
        // S 0123456 7P SS
        // L HLHLHLH LL HH
        if( ( channel->GetBitState() == BIT_LOW ) )
        {
            sync_start = channel->GetSampleNumber();
            bit_rate = channel->GetSampleOfNextEdge() - channel->GetSampleNumber();
            mResults->AddMarker( sync_start + ( bit_rate / 2 ), AnalyzerResults::Start, mSettings->mInputChannel );
            sync_bit_count++;
        }
        else
        {
            Identify( "IDLE", FLAG_IDLE, 0xFF );
            sync_bit_count = 0;
        }
    }
    else if( sync_bit_count < 8 )
    {
        // Check the widths of subsequent single wide-bits
        if( !Valid( ( sync_bit_count & 0x01 ) ? BIT_HIGH : BIT_LOW ) )
        {
            sync_bit_count = 0;
            sync_start = 0;
        }
        else
        {
            sync_bit_count++;
            mResults->AddMarker( channel->GetSampleNumber() + ( bit_rate / 2 ), AnalyzerResults::Dot, mSettings->mInputChannel );
        }
    }
    else if( sync_bit_count == 8 )
    {
        if( !Valid( BIT_LOW, bit_rate * 2 ) )
        {
            sync_bit_count = 0;
            sync_start = 0;
        }
        else
        {
            sync_bit_count++;
            mResults->AddMarker( channel->GetSampleNumber() + ( bit_rate / 2 ), AnalyzerResults::Dot, mSettings->mInputChannel );
            mResults->AddMarker( channel->GetSampleNumber() + ( bit_rate * 1.5 ), AnalyzerResults::Square, mSettings->mInputChannel );
        }
    }
    else
    {
        if( !Valid( BIT_HIGH, bit_rate * 2 ) )
        {
            sync_bit_count = 0;
            sync_start = 0;
        }
        else
        {
            U64 bit_rate = ( channel->GetSampleNumber() - sync_start ) / 10;

            mResults->AddMarker( channel->GetSampleNumber() + ( bit_rate / 2 ), AnalyzerResults::Stop, mSettings->mInputChannel );
            mResults->AddMarker( channel->GetSampleNumber() + ( bit_rate * 1.5 ), AnalyzerResults::Stop, mSettings->mInputChannel );
            channel->Advance( bit_rate );

            Identify( sync_start, "SYNC", FLAG_SYNC, bit_rate );
            sync_start = 0;
            sync_bit_count = 0;
            return false;
        }
    }

    // Default is that we are not synced
    return true;
}

// We have synchronized our bit rate, return:
//      true:   We are still synchronized
//      false:  We are not synchronized

bool ll_analyzer::synced()
{
    static U8 data_bit_count = 0;
    static U64 data_start_bit = 0;
    static U16 data_value;

    mResults->AddMarker( channel->GetSampleNumber(), channel->GetBitState() ? AnalyzerResults::UpArrow : AnalyzerResults::DownArrow,
                         mSettings->mInputChannel );

    U64 bit_width = channel->GetSampleOfNextEdge() - channel->GetSampleNumber();
    if( ( channel->GetBitState() == BIT_LOW ) && ( bit_width > bit_rate * 13 ) )
    {
        // BREAK
        Identify( "BREAK", FLAG_BREAK, 0x00 );
        data_bit_count = 0;
        return false;
    }

    if( bit_width < ( bit_rate * .75 ) )
    {
        // Too small, could be a speed change
        // Immediately jump to an unsynced condition at the current bit
        // Identify( "NARROW", FLAG_NARROW );
        // data_bit_count = 0;
        unsynced();
        return false;
    }

    if( channel->GetBitState() == BIT_HIGH && data_bit_count == 0 )
    {
        // IDLE
        Identify( "IDLE", FLAG_IDLE, 0xFF );
        data_bit_count = 0;
        return true;
    }

    if( channel->GetBitState() == BIT_LOW && data_bit_count == 0 )
    {
        // START BIT
        data_bit_count = 1;
    }

    // Are we in the middle of a byte?
    if( data_bit_count )
    {
        channel->Advance( ( bit_rate / 2 ) );
        // Process as many logical bits as there are in this physical pulse
        while( true )
        {
            // Process the Bit
            switch( data_bit_count )
            {
            case 1:
                data_value = 0;
                data_start_bit = channel->GetSampleNumber();
                mResults->AddMarker( data_start_bit, AnalyzerResults::Start, mSettings->mInputChannel );
                break;
            case 2 ... 9:
                mResults->AddMarker( channel->GetSampleNumber(), channel->GetBitState() ? AnalyzerResults::One : AnalyzerResults::Zero,
                                     mSettings->mInputChannel );
                if( channel->GetBitState() )
                    data_value += ( 1 << ( data_bit_count - 2 ) );
                break;
            case 10:
                // Parity
                mResults->AddMarker( channel->GetSampleNumber(), AnalyzerResults::Square, mSettings->mInputChannel );
                break;
            case 11:
                // Stop bit 1
                mResults->AddMarker( channel->GetSampleNumber(), AnalyzerResults::Stop, mSettings->mInputChannel );
                break;
            case 12:
                // Stop bit 2
                mResults->AddMarker( channel->GetSampleNumber(), AnalyzerResults::Stop, mSettings->mInputChannel );
                data_bit_count = 0;

                if( data_value == 0x55 )
                {
                    // bit_rate = ( channel->GetSampleOfNextEdge() - data_start_bit ) / 12;
                    Identify( data_start_bit, "SYNC", FLAG_SYNC, 0x55 );
                }
                else
                {
                    Identify( data_start_bit, "DATA", FLAG_DATA, data_value );
                    // Is the spacing remaining after the last bit large enough to call out as
                    // an official idle
                    if ((channel->GetSampleOfNextEdge() - channel->GetSampleNumber()) > (bit_rate * 13)) {
                        Identify("IDLE", FLAG_IDLE, 0xFF);
                    }
                }
                return true;
                break;
            }
            data_bit_count++;
            bit_width -= bit_rate;

            if( bit_width <= ( bit_rate * .5 ) )
                break;

            channel->Advance( bit_rate );
        };
    }

    return true;
}

void ll_analyzer::WorkerThread()
{
    bool is_synced = false;
    U64 this_width = 0;
    channel = GetAnalyzerChannelData( mSettings->mInputChannel );

    // We should start at high state (IDLE) at the beginning of a capture
    // If we are starting low consider it an initial break
    if( channel->GetBitState() == BIT_LOW )
    {
        Identify( "BREAK", FLAG_BREAK, 0x00 );
        channel->AdvanceToNextEdge();
    }

    // We don't know rate yet, until we get our first SYNC
    updi_state state = updi_state::SYNC;

    for( ;; )
    {
        is_synced = is_synced ? synced() : !unsynced();

        mResults->CommitResults();
        ReportProgress( channel->GetSampleNumber() );

        channel->AdvanceToNextEdge();

        CheckIfThreadShouldExit();
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
