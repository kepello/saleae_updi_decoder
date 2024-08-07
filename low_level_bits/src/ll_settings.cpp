#include "ll_settings.h"

#include <AnalyzerHelpers.h>
#include <sstream>
#include <cstring>

#pragma warning( disable : 4800 ) // warning C4800: 'U32' : forcing value to bool 'true' or 'false' (performance warning)

ll_settings::ll_settings()
    : mInputChannel( UNDEFINED_CHANNEL )
{
    mInputChannelInterface.reset( new AnalyzerSettingInterfaceChannel() );
    mInputChannelInterface->SetTitleAndTooltip( "Input Channel", "UPDI Protocol" );
    mInputChannelInterface->SetChannel( mInputChannel );

    AddInterface( mInputChannelInterface.get() );

    // AddExportOption( 0, "Export as text/csv file", "text (*.txt);;csv (*.csv)" );
    AddExportOption( 0, "Export as text/csv file" );
    AddExportExtension( 0, "text", "txt" );
    AddExportExtension( 0, "csv", "csv" );

    ClearChannels();
    AddChannel( mInputChannel, "UPDI", false );
}

ll_settings::~ll_settings() = default;

bool ll_settings::SetSettingsFromInterfaces()
{
    mInputChannel = mInputChannelInterface->GetChannel();
    ClearChannels();
    AddChannel( mInputChannel, "UPDI", true );
    return true;
}

void ll_settings::UpdateInterfacesFromSettings()
{
    mInputChannelInterface->SetChannel( mInputChannel );
}

void ll_settings::LoadSettings( const char* settings )
{
    SimpleArchive text_archive;
    text_archive.SetString( settings );

    const char* name_string; // the first thing in the archive is the name of the protocol analyzer that the data belongs to.
    text_archive >> &name_string;
    if( strcmp( name_string, "UPDI" ) != 0 )
        AnalyzerHelpers::Assert( "UPDI: Provided with a settings string that doesn't belong to us;" );

    text_archive >> mInputChannel;

    ClearChannels();
    AddChannel( mInputChannel, "UPDI", true );

    UpdateInterfacesFromSettings();
}

const char* ll_settings::SaveSettings()
{
    SimpleArchive text_archive;

    text_archive << ANALYZER_NAME;
    text_archive << mInputChannel;

    return SetReturnString( text_archive.GetString() );
}
