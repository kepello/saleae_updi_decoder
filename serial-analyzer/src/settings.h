#pragma once
#include <AnalyzerSettings.h>
#include <AnalyzerTypes.h>

#include <memory>


#define LL_ANALYZER_NAME "UPDI Serial"
#define LL_ANALYZER_SETTINGS "UPDISerial"
#define LL_CHANNEL_NAME "UPDI Serial"

namespace SerialAnalyzerEnums
{
    enum Mode
    {
        Normal,
        MpModeMsbZeroMeansAddress,
        MpModeMsbOneMeansAddress
    };
}

class SerialAnalyzerSettings : public AnalyzerSettings
{
  public:
    SerialAnalyzerSettings();
    virtual ~SerialAnalyzerSettings();

    virtual bool SetSettingsFromInterfaces();
    void UpdateInterfacesFromSettings();
    virtual void LoadSettings( const char* settings );
    virtual const char* SaveSettings();

    Channel mInputChannel;
    U32 mBitRate;

  protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;

};

