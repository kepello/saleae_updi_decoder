#include "results.h"
#include <AnalyzerHelpers.h>
#include "analyzer.h"
#include "settings.h"
#include <iostream>
#include <sstream>


updi_results::updi_results( updi_analyzer* analyzer, updi_settings* settings )
    : AnalyzerResults(), mSettings( settings ), mAnalyzer( analyzer )
{
}

updi_results::~updi_results() = default;

void updi_results::GenerateBubbleText( U64 frame_index, Channel& /*channel*/,
                                       DisplayBase display_base ) // unreferenced vars commented out to remove warnings.
{
    // we only need to pay attention to 'channel' if we're making bubbles for more than one channel (as set by
    // AddChannelBubblesWillAppearOn)
    ClearResultStrings();
    Frame frame = GetFrame( frame_index );

    bool framing_error = false;
    if( ( frame.mFlags & FRAMING_ERROR_FLAG ) != 0 )
        framing_error = true;

    bool parity_error = false;
    if( ( frame.mFlags & PARITY_ERROR_FLAG ) != 0 )
        parity_error = true;

    U32 bits_per_transfer = 8;

    char number_str[ 128 ];
    AnalyzerHelpers::GetNumberString( frame.mData1, display_base, bits_per_transfer, number_str, 128 );

    char result_str[ 128 ];

    // normal case:
    if( ( parity_error == true ) || ( framing_error == true ) )
    {
        AddResultString( "!" );

        snprintf( result_str, sizeof( result_str ), "%s (error)", number_str );
        AddResultString( result_str );

        if( framing_error == false )
            snprintf( result_str, sizeof( result_str ), "%s (parity error)", number_str );
        else if( parity_error == false )
            snprintf( result_str, sizeof( result_str ), "%s (framing error)", number_str );
        else
            snprintf( result_str, sizeof( result_str ), "%s (framing error & parity error)", number_str );

        AddResultString( result_str );
    }
    else
    {
        AddResultString( number_str );
    }
}

void updi_results::GenerateExportFile( const char* file, DisplayBase display_base, U32 /*export_type_user_id*/ )
{
    // export_type_user_id is only important if we have more than one export type.
    std::stringstream ss;

    U64 trigger_sample = mAnalyzer->GetTriggerSample();
    U32 sample_rate = mAnalyzer->GetSampleRate();
    U64 num_frames = GetNumFrames();

    void* f = AnalyzerHelpers::StartFile( file );


    // Normal case -- not MP mode.
    ss << "Time [s],Value,Parity Error,Framing Error" << std::endl;

    for( U32 i = 0; i < num_frames; i++ )
    {
        Frame frame = GetFrame( i );

        // static void GetTimeString( U64 sample, U64 trigger_sample, U32 sample_rate_hz, char* result_string, U32
        // result_string_max_length );
        char time_str[ 128 ];
        AnalyzerHelpers::GetTimeString( frame.mStartingSampleInclusive, trigger_sample, sample_rate, time_str, 128 );

        char number_str[ 128 ];
        AnalyzerHelpers::GetNumberString( frame.mData1, display_base, 8, number_str, 128 );

        ss << time_str << "," << number_str;

        if( ( frame.mFlags & PARITY_ERROR_FLAG ) != 0 )
            ss << ",Error,";
        else
            ss << ",,";

        if( ( frame.mFlags & FRAMING_ERROR_FLAG ) != 0 )
            ss << "Error";


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

void updi_results::GenerateFrameTabularText( U64 frame_index, DisplayBase display_base )
{
    ClearTabularText();
    Frame frame = GetFrame( frame_index );

    bool framing_error = false;
    if( ( frame.mFlags & FRAMING_ERROR_FLAG ) != 0 )
        framing_error = true;

    bool parity_error = false;
    if( ( frame.mFlags & PARITY_ERROR_FLAG ) != 0 )
        parity_error = true;

    U32 bits_per_transfer = 8;

    char number_str[ 128 ];
    AnalyzerHelpers::GetNumberString( frame.mData1, display_base, bits_per_transfer, number_str, 128 );

    char result_str[ 128 ];

    // normal case:
    if( ( parity_error == true ) || ( framing_error == true ) )
    {
        if( framing_error == false )
            snprintf( result_str, sizeof( result_str ), "%s (parity error)", number_str );
        else if( parity_error == false )
            snprintf( result_str, sizeof( result_str ), "%s (framing error)", number_str );
        else
            snprintf( result_str, sizeof( result_str ), "%s (framing error & parity error)", number_str );

        AddTabularText( result_str );
    }
    else
    {
        AddTabularText( number_str );
    }
}

void updi_results::GeneratePacketTabularText( U64 /*packet_id*/,
                                              DisplayBase /*display_base*/ ) // unreferenced vars commented out to remove warnings.
{
    ClearResultStrings();
    AddResultString( "not supported" );
}

void updi_results::GenerateTransactionTabularText( U64 /*transaction_id*/,
                                                   DisplayBase /*display_base*/ ) // unreferenced vars commented out to remove warnings.
{
    ClearResultStrings();
    AddResultString( "not supported" );
}
