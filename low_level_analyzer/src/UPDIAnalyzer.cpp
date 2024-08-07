#include "UPDIAnalyzer.h"
#include "UPDIAnalyzerSettings.h"
#include <AnalyzerChannelData.h>
#include <AnalyzerResults.h>

// Check for data
int UPDIAnalyzer::isData() {
    int data = 0;
    U64 data_start = mUPDI->GetSampleNumber();

    // Data follows a Start Bit
    if (mUPDI->GetBitState()!=BIT_LOW) return -1;
    
    // Advance to first bit
    mUPDI->AdvanceToNextEdge();

    // If we don't have a bit width yet, approximate with two bits
    if (bit_width == 0) {
        bit_width = (mUPDI->GetSampleOfNextEdge() - data_start)/2;
    }

    // Get 8 data bits 
    data = 0;
    bool is_error = false;
    U8 even_count = 0;

    // Advance to the middle of the bits
    mUPDI->Advance(bit_width/2);
    for (int b=0; b<8; b++) {

        // Get that bit value
        if (mUPDI->GetBitState()==BIT_HIGH) {
            data += (1<<b);
            even_count++;
        }

        // Mark them
        mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    }

    // Parity 
    mUPDI->Advance(bit_width);
    if ((mUPDI->GetBitState()==BIT_HIGH) && (even_count&1)) {
        mResults->AddMarker(
                mUPDI->GetSampleNumber(),
                AnalyzerResults::X,
                mSettings->mInputChannel);
        is_error = true;
    } else {
        mResults->AddMarker(
                mUPDI->GetSampleNumber(),
                AnalyzerResults::Square,
                mSettings->mInputChannel);
    }

    // Stop Bit
    mUPDI->Advance(bit_width);
    if (mUPDI->GetBitState() != BIT_HIGH) {
        mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::X,
            mSettings->mInputChannel);
        is_error = true;
    } else {
        mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Square,
            mSettings->mInputChannel);
    }

    // Stop Bit
    mUPDI->Advance(bit_width);
    if (mUPDI->GetBitState() != BIT_HIGH) {
        mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::X,
            mSettings->mInputChannel);
        is_error = true;
    } else {
        mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Square,
            mSettings->mInputChannel);
    }

    // Back to regular spacing
    mUPDI->Advance(bit_width/2);

    if (is_error) return -1;
    return data;
}

// Check for a SYNC bit
bool UPDIAnalyzer::isSync() {
    U64 sync_start = mUPDI->GetSampleNumber();
    // Start Bit
    if (mUPDI->GetBitState() != BIT_LOW) return false; // Start
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // 0
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_LOW) return false; // 1
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // 2
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_LOW) return false; // 3
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // 4
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_LOW) return false; // 5
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // 6
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_LOW) return false;  // 7
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Dot,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_LOW) return false;  // Parity
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Square,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // Stop
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Square,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();
    if (mUPDI->GetBitState() != BIT_HIGH) return false; // Stop
            mResults->AddMarker(
            mUPDI->GetSampleNumber(),
            AnalyzerResults::Square,
            mSettings->mInputChannel);
    mUPDI->AdvanceToNextEdge();

    // After all 12 bits we can get the best approximation of rate
    bit_width = (mUPDI->GetSampleNumber()-sync_start)/12;
    return true;
}

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

void UPDIAnalyzer::Update() 
{
    mResults->CommitResults();
    ReportProgress( mUPDI->GetSampleNumber() );
    CheckIfThreadShouldExit();
}

void UPDIAnalyzer::WorkerThread()
{

    mUPDI = GetAnalyzerChannelData( mSettings->mInputChannel );
    U64 bit_width=0;
    U64 this_transition;
    U64 data_start;
    bool is_error = false;
    U8 even_count = 0;

    U8 data;

    // Starting low probably means sampling but no activity yet, advance to first HIGH
    if (mUPDI->GetBitState()==BIT_LOW) {
        mUPDI->AdvanceToNextEdge();
    } 

    // Loop forever (Starting HIGH)
    for( ;; )
    {
        U64 loop_start = mUPDI->GetSampleNumber();
        mResults->AddMarker(mUPDI->GetSampleNumber(),AnalyzerResults::Start, mSettings->mInputChannel);

        // HIGH = Idle
        if (mUPDI->GetBitState() == BIT_HIGH) {
            // This is an idle state, move to the next transition (LOW state)
            mUPDI->AdvanceToNextEdge();
            Notate(loop_start, mUPDI->GetSampleNumber(), "IDLE", FrameFlags::IDLE); 
        } 
    
        // Low, Presume Start Bit
        this_transition = mUPDI->GetSampleNumber();

        // Look for data/sync
        int byte = isData();
        if (byte != -1) {
            Notate(this_transition, mUPDI->GetSampleNumber(), "DATA", FrameFlags::DATA, (U8)byte);
        }

            // // Is this a break?
            // if ((bit_width>0) && (mUPDI->GetSampleOfNextEdge() - mUPDI->GetSampleNumber() > (bit_width * 12.5))) {
            //     // BREAK detected, reset
            //     mUPDI->AdvanceToNextEdge();
            //     Notate(mUPDI->GetSampleNumber(), mUPDI->GetSampleNumber(), "BREAK" , FrameFlags::BREAK);
            //     Update();
            //     continue;
            // } 

            // Must be a start bit
            // mResults->AddMarker(mUPDI->GetSampleNumber(),AnalyzerResults::Start,mSettings->mInputChannel);

            // Look ahead to next bit to calculate possible bit width change
            // Note:  One bit can vary, but two is relatively precise.
            
            // // Look ahead at the next bit width, for a width change
            // U64 this_width = (mUPDI->GetSampleOfNextEdge() - this_transition)/2;

            // if ((bit_width == 0) || (this_width < (bit_width * .9))) {
            //     // This bit is too small to be a start bit at our current rate
            //     // Recalculate projected rate
            //     bit_width = this_width;
            //     Notate(this_transition, mUPDI->GetSampleNumber(), "RATE", FrameFlags::RATE);
            // } else {
            //     // Regular Start Big
            //     Notate(this_transition, mUPDI->GetSampleNumber(), "START", FrameFlags::START);
            // }

            
            // // Handle an error, drop the data
            // if (!is_error) {
            //     Notate(data_start, mUPDI->GetSampleNumber(), "DATA", FrameFlags::DATA, data);
            // } else {
            //     Notate(data_start, mUPDI->GetSampleNumber(), "ERROR", FrameFlags::ERROR, data);
            // }
        
        Update();
    }
}


void UPDIAnalyzer::Notate(U64 start, U64 end,const char* note, FrameFlags flag, int value) {
    
    Frame frame;
    frame.mStartingSampleInclusive = static_cast<S64>( start+1);
    frame.mEndingSampleInclusive = static_cast<S64>( end-1);
    frame.mData1 = (U64)value;
    frame.mFlags = flag;
    mResults->AddFrame( frame );

    FrameV2 frameV2;
    if (value != -1)
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
