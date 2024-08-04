#ifndef UPDI_ANALYZER_SETTINGS
#define UPDI_ANALYZER_SETTINGS

#include <AnalyzerSettings.h>
#include <AnalyzerTypes.h>
#include <memory>

class UPDIAnalyzerSettings : public AnalyzerSettings
{
  public:
    UPDIAnalyzerSettings();
    virtual ~UPDIAnalyzerSettings();

    virtual bool SetSettingsFromInterfaces();
    void UpdateInterfacesFromSettings();
    virtual void LoadSettings( const char* settings );
    virtual const char* SaveSettings();

    Channel mInputChannel;

  protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;

};

#endif // UPDI_ANALYZER_SETTINGS
