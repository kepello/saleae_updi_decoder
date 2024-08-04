#include "UPDIAnalyzer.h"
#include "UPDIAnalyzerSettings.h"
#include <AnalyzerChannelData.h>
#include <AnalyzerResults.h>

UPDIAnalyzer::UPDIAnalyzer() : Analyzer2(), mSettings( new UPDIAnalyzerSettings() )
{
    SetAnalyzerSettings( mSettings.get() );
    UseFrameV2();
}

UPDIAnalyzer::~UPDIAnalyzer()
{
    KillThread();
}


void UPDIAnalyzer::SetupResults()
{
    // Unlike the worker thread, this function is called from the GUI thread
    // we need to reset the Results object here because it is exposed for direct access by the GUI, and it can't be deleted from the
    // WorkerThread

    mResults.reset( new UPDIAnalyzerResults( this, mSettings.get() ) );
    SetAnalyzerResults( mResults.get() );
    mResults->AddChannelBubblesWillAppearOn( mSettings->mInputChannel );
}

bool UPDIAnalyzer::NextBit(BitState expected_bit) {
    // From where we are
    U64 last_transition = mUPDI->GetSampleNumber();
    // Go forward to the middle of the the anticipated next bit
    mUPDI->Advance(bit_width/2);
    // Get that bit value
    BitState this_bit = mUPDI->GetBitState();
    mUPDI->Advance(bit_width/2);
    // Is it a match?
    return (this_bit == expected_bit);
}

enum UPDIState
{
    STARTUP,
    IDLE,
    DATA,
    ERROR
};

void UPDIAnalyzer::WorkerThread()
{
    mUPDI = GetAnalyzerChannelData( mSettings->mInputChannel );
    BitState bit;

    U64 last_transition;
    U64 this_transition;
    U64 next_transition;
    U64 data_start;
    U64 sync_start;

    UPDIState state = STARTUP;

    U32 this_width;
    U8 data;

    // Starting low probably means sampling but no activity yet, advance to first HIGH
    if (mUPDI->GetBitState()==BIT_LOW) {
        mUPDI->AdvanceToNextEdge();
    } 

    // Loop forever
    for( ;; )
    {
        switch( state )
        {
            case STARTUP:

                // We should always begin checking on LOW of a new potential start bit
                if (mUPDI->GetBitState()==BIT_HIGH) {
                    mUPDI->AdvanceToNextEdge();
                }

                // Currently at beginning (LOW) of bit
                last_transition = sync_start= mUPDI->GetSampleNumber();

                // Look ahead to end of bit, which will be HIGH
                next_transition = mUPDI->GetSampleOfNextEdge();
                
                // Calculate the Bit Width
                bit_width = next_transition - last_transition;;
                
                // Go to the end of the Bit
                mUPDI->AdvanceToNextEdge();

                // First bit was START Bit (LOW)  // Start
                if (!NextBit(BIT_HIGH)) break;    // 0
                if (!NextBit(BIT_LOW)) break;    // 1 
                if (!NextBit(BIT_HIGH))  break;    // 2
                if (!NextBit(BIT_LOW)) break;    // 3
                if (!NextBit(BIT_HIGH))  break;    // 4
                if (!NextBit(BIT_LOW)) break;    // 5
                if (!NextBit(BIT_HIGH))  break;    // 6
                if (!NextBit(BIT_LOW)) break;    // 7
                if (!NextBit(BIT_LOW))  break;    // Parity
                if (!NextBit(BIT_HIGH)) break;    // Stop
                if (!NextBit(BIT_HIGH)) break;    // Stop

                this_transition = mUPDI->GetSampleNumber();

                // Calculate bit rate using all bits to get better average
                bit_width = (this_transition - sync_start)/12;
                Notate(sync_start, this_transition - (bit_width/2), 0x55, "sync");
                state = IDLE;
                break;

            case IDLE:

                // Next is either Data, Break, SYNC, ACK or Idle
                this_transition = mUPDI->GetSampleNumber();

                // If we are HIGH it is an idle condition
                if (mUPDI->GetBitState()== BIT_HIGH) {
                    // This is an idle state, move to the next transition
                    last_transition = this_transition;
                    mUPDI->AdvanceToNextEdge();
                    this_transition = mUPDI->GetSampleNumber();
                }

                // Low is either Start Bit (Data, Sync or Ack) or else Break
                this_width = mUPDI->GetSampleOfNextEdge() - this_transition;
                if (this_width > (bit_width * 12.5)) {
                    // BREAK detected, reset
                    mUPDI->AdvanceToNextEdge();
                    Notate(this_transition, mUPDI->GetSampleNumber(), 0xFF, "BREAK");
                    state = STARTUP;
                    break;
                } else if (this_width < (bit_width * .9)) {
                    // This bit is too small to be at our current rate
                    // We might have a bit rate change, need to re-sync
                    //mResults->AddMarker(mUPDI->GetSampleNumber()+1,AnalyzerResults::One,mSettings->mInputChannel);
                    state = STARTUP;
                    break;
                } 

                // Looks like data
                state = DATA;
                break;
                
            case DATA:
                
                // Expect Start bit
                data_start = mUPDI->GetSampleNumber();
                if (!NextBit(BIT_LOW)) {state=ERROR; break;}

                // Advance for middle of bits
                mUPDI->Advance(bit_width/2);
                // Get 8 data bits
                data = 0;
                for (int b=0; b<8; b++) {
                    //mResults->AddMarker(mUPDI->GetSampleNumber(),AnalyzerResults::Dot,mSettings->mInputChannel);
                    if (mUPDI->GetBitState())                     
                        data += 1<<b;
                    mUPDI->Advance(bit_width);
                }
                // Parity -- Ignore it
                //mResults->AddMarker(mUPDI->GetSampleNumber(),AnalyzerResults::Square,mSettings->mInputChannel);
                mUPDI->Advance(bit_width/2);

                // 2 Stop Bits
                if (!NextBit(BIT_HIGH)) {state=ERROR; break;}
                if (!NextBit(BIT_HIGH)) {state=ERROR; break;}    

                // Notate the value
                Notate(data_start, mUPDI->GetSampleNumber()-(bit_width/2), data, "data");

                state=IDLE;
                break;

            case ERROR:
                Notate(data_start+1, mUPDI->GetSampleNumber()-1, 0x00, "ERROR");
                state = STARTUP;
                break;
        }

        mResults->CommitResults();
        ReportProgress( this_transition );
        CheckIfThreadShouldExit();
    }
}


void UPDIAnalyzer::Notate(U64 start, U64 end, U64 value, const char* note) {
        
    Frame frame;
    frame.mStartingSampleInclusive = static_cast<S64>( start+1);
    frame.mEndingSampleInclusive = static_cast<S64>( end-1);
    frame.mData1 = value;
    frame.mFlags = 0;
    mResults->AddFrame( frame );

    FrameV2 frameV2;
    frameV2.AddByte( "data", value );
    mResults->AddFrameV2( frameV2, note, start+1, end-1 );
    mResults->CommitResults();
    
}


bool UPDIAnalyzer::NeedsRerun()
{
    return false;
}

U32 UPDIAnalyzer::GenerateSimulationData( U64 minimum_sample_index, U32 device_sample_rate,
                                          SimulationChannelDescriptor** simulation_channels )
{
    return 0;
}


U32 UPDIAnalyzer::GetMinimumSampleRateHz()
{
    return 200000 * 4;
}

const char* UPDIAnalyzer::GetAnalyzerName() const
{
    return "UPDI";
}

const char* GetAnalyzerName()
{
    return "UPDI";
}

Analyzer* CreateAnalyzer()
{
    return new UPDIAnalyzer();
}

void DestroyAnalyzer( Analyzer* analyzer )
{
    delete analyzer;
}
