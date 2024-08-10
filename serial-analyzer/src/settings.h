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
    U32 mBitsPerTransfer;
    AnalyzerEnums::ShiftOrder mShiftOrder;
    double mStopBits;
    AnalyzerEnums::Parity mParity;
    bool mInverted;
    bool mUseAutobaud;
    SerialAnalyzerEnums::Mode mSerialMode;

  protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;
    std::unique_ptr<AnalyzerSettingInterfaceInteger> mBitRateInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mBitsPerTransferInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mShiftOrderInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mStopBitsInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mParityInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mInvertedInterface;
    std::unique_ptr<AnalyzerSettingInterfaceBool> mUseAutobaudInterface;
    std::unique_ptr<AnalyzerSettingInterfaceNumberList> mSerialModeInterface;
};

