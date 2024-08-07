#ifndef LL_ANALYZER_SETTINGS
#define LL_ANALYZER_SETTINGS

#define ANALYZER_NAME "BITS"

#include <AnalyzerSettings.h>
#include <AnalyzerTypes.h>
#include <memory>

class ll_settings : public AnalyzerSettings
{
  public:
    ll_settings();
    virtual ~ll_settings();

    virtual bool SetSettingsFromInterfaces();
    void UpdateInterfacesFromSettings();
    virtual void LoadSettings( const char* settings );
    virtual const char* SaveSettings();

    Channel mInputChannel;

  protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;

};

#endif // LL_ANALYZER_SETTINGS
