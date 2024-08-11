#include "ll_results.h"
#include <AnalyzerHelpers.h>
#include "ll_analyzer.h"
#include "ll_settings.h"
#include <iostream>
#include <sstream>


ll_results::ll_results( ll_analyzer* analyzer, ll_settings* settings )
    : AnalyzerResults(), mSettings( settings ), mAnalyzer( analyzer )
{
}

ll_results::~ll_results() = default;

void ll_results::GenerateBubbleText( U64 frame_index, Channel& /*channel*/,
                                              DisplayBase display_base ) // unreferenced vars commented out to remove warnings.
{
    ClearResultStrings();
    Frame frame = GetFrame( frame_index );
    U32 bits_per_transfer = 8;

    switch (frame.mFlags)
    {
        case FLAG_DATA:
        case FLAG_NONE:
            char number_str[ 128 ];
            AnalyzerHelpers::GetNumberString( frame.mData1, display_base, bits_per_transfer, number_str, 128 );
            AddResultString( number_str );
            break;
        case FLAG_WRONG_BIT:
            AddResultString("WRONG");
            break;
        case FLAG_WIDE:
            AddResultString("WIDE");
            break;
        case FLAG_NARROW:
            AddResultString("NARROW");
            break;
        case FLAG_SYNC:
            AddResultString("SYNC");
            break;
        case FLAG_IDLE:
            AddResultString("IDLE");
            break;
        case FLAG_BREAK:
            AddResultString("BREAK");
            break;
        case FLAG_ACK:
            AddResultString("ACT");
            break;
        case FLAG_RATE:
            AddResultString("RATE");
            break;
        case FLAG_START:
            AddResultString("START");
            break;
    }
    
}

void ll_results::GenerateExportFile( const char* file, DisplayBase display_base, U32 /*export_type_user_id*/ )
{
    // export_type_user_id is only important if we have more than one export type.
    std::stringstream ss;

    U64 trigger_sample = mAnalyzer->GetTriggerSample();
    U32 sample_rate = mAnalyzer->GetSampleRate();
    U64 num_frames = GetNumFrames();

    void* f = AnalyzerHelpers::StartFile( file );

    // Normal case -- not MP mode.
    ss << "Time [s],Value" << std::endl;

    for( U32 i = 0; i < num_frames; i++ )
    {
        Frame frame = GetFrame( i );

        char time_str[ 128 ];
        AnalyzerHelpers::GetTimeString( frame.mStartingSampleInclusive, trigger_sample, sample_rate, time_str, 128 );

        char number_str[ 128 ];
        AnalyzerHelpers::GetNumberString( frame.mData1, display_base, 8, number_str, 128 );

        ss << time_str << "," << number_str;

        ss << std::endl;

        AnalyzerHelpers::AppendToFile( ( U8* )ss.str().c_str(), static_cast<U32>( ss.str().length() ), f );
        ss.str( std::string() );

        if( UpdateExportProgressAndCheckForCancel( i, num_frames ) == true )
        {
            AnalyzerHelpers::EndFile( f );
            return;
        }
    }


    UpdateExportProgressAndCheckForCancel( num_frames, num_frames );
    AnalyzerHelpers::EndFile( f );
}

void ll_results::GenerateFrameTabularText( U64 frame_index, DisplayBase display_base )
{
    ClearTabularText();
    Frame frame = GetFrame( frame_index );
    U32 bits_per_transfer = 8;
    char number_str[ 128 ];
    AnalyzerHelpers::GetNumberString( frame.mData1, display_base, bits_per_transfer, number_str, 128 );
    char result_str[ 128 ];
    AddTabularText( number_str );
}

void ll_results::GeneratePacketTabularText( U64 /*packet_id*/,
                                                     DisplayBase /*display_base*/ ) // unreferenced vars commented out to remove warnings.
{
    ClearResultStrings();
    AddResultString( "not supported" );
}

void ll_results::GenerateTransactionTabularText(
    U64 /*transaction_id*/, DisplayBase /*display_base*/ ) // unreferenced vars commented out to remove warnings.
{
    ClearResultStrings();
    AddResultString( "not supported" );
}
