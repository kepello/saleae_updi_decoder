#include "settings.h"

#include <AnalyzerHelpers.h>
#include <sstream>
#include <cstring>

#pragma warning( disable : 4800 ) // warning C4800: 'U32' : forcing value to bool 'true' or 'false' (performance warning)

SerialAnalyzerSettings::SerialAnalyzerSettings()
    : mInputChannel( UNDEFINED_CHANNEL ),
      mBitRate( 100000 ),
      mBitsPerTransfer( 8 ),
      mStopBits( 2.0 ),
      mParity( AnalyzerEnums::Even ),
      mShiftOrder( AnalyzerEnums::LsbFirst ),
      mInverted( false ),
      mUseAutobaud( false ),
      mSerialMode( SerialAnalyzerEnums::Normal )
{
    mInputChannelInterface.reset( new AnalyzerSettingInterfaceChannel() );
    mInputChannelInterface->SetTitleAndTooltip( "Input Channel", LL_ANALYZER_NAME );
    mInputChannelInterface->SetChannel( mInputChannel );

    AddExportOption( 0, "Export as text/csv file" );
    AddExportExtension( 0, "text", "txt" );
    AddExportExtension( 0, "csv", "csv" );

    ClearChannels();
    AddChannel( mInputChannel, LL_CHANNEL_NAME, false );
}

SerialAnalyzerSettings::~SerialAnalyzerSettings() = default;

bool SerialAnalyzerSettings::SetSettingsFromInterfaces()
{

    mInputChannel = mInputChannelInterface->GetChannel();

    ClearChannels();
    AddChannel( mInputChannel, LL_CHANNEL_NAME, true );

    return true;
}

void SerialAnalyzerSettings::UpdateInterfacesFromSettings()
{
    mInputChannelInterface->SetChannel( mInputChannel );
}

void SerialAnalyzerSettings::LoadSettings( const char* settings )
{
    SimpleArchive text_archive;
    text_archive.SetString( settings );

    const char* name_string; // the first thing in the archive is the name of the protocol analyzer that the data belongs to.
    text_archive >> &name_string;
    if( strcmp( name_string, LL_ANALYZER_SETTINGS ) != 0 )
        AnalyzerHelpers::Assert( "Provided with a settings string that doesn't belong to us;" );

    text_archive >> mInputChannel;

    ClearChannels();
    AddChannel( mInputChannel, LL_CHANNEL_NAME, true );

    UpdateInterfacesFromSettings();
}

const char* SerialAnalyzerSettings::SaveSettings()
{
    SimpleArchive text_archive;

    text_archive << LL_ANALYZER_SETTINGS;
    text_archive << mInputChannel;

    return SetReturnString( text_archive.GetString() );
}
