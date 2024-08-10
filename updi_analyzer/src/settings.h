#pragma once
#include <AnalyzerSettings.h>
#include <AnalyzerTypes.h>

#include <memory>


#define LL_ANALYZER_NAME "UPDI Serial"
#define LL_ANALYZER_SETTINGS "UPDISerial"
#define LL_CHANNEL_NAME "UPDI Serial"

#define BITS_PER_TRANSFER 8

class updi_settings : public AnalyzerSettings
{
  public:
    updi_settings();
    virtual ~updi_settings();

    virtual bool SetSettingsFromInterfaces();
    void UpdateInterfacesFromSettings();
    virtual void LoadSettings( const char* settings );
    virtual const char* SaveSettings();

    Channel mInputChannel;
    U32 mBitRate;

  protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;
};
