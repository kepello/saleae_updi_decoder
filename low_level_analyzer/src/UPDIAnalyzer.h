#ifndef UPDI_ANALYZER_H
#define UPDI_ANALYZER_H

//#define LOGIC2

#include <Analyzer.h>
#include "UPDIAnalyzerResults.h"


enum FrameFlags {
    IDLE, BREAK, SYNC, DATA, ACK, ERROR, START, RATE
};



class UPDIAnalyzerSettings;
class UPDIAnalyzer : public Analyzer2
{
  public:
    UPDIAnalyzer();
    bool isSync();
    int isData();
    virtual ~UPDIAnalyzer();
    virtual void SetupResults();
    virtual void WorkerThread();

    virtual U32 GenerateSimulationData( U64 newest_sample_requested, U32 sample_rate, SimulationChannelDescriptor** simulation_channels );
    virtual U32 GetMinimumSampleRateHz();

    virtual const char* GetAnalyzerName() const;
    virtual bool NeedsRerun();
    virtual void Notate(U64 start, U64 end, const char* note, FrameFlags flag, int value=-1 );
    virtual void Update();

#pragma warning( push )
#pragma warning(                                                                                                                           \
    disable : 4251 ) // warning C4251: 'UPDIAnalyzer::<...>' : class <...> needs to have dll-interface to be used by clients of class

  protected: // functions
    void ComputeSampleOffsets();

  protected: // vars
    std::unique_ptr<UPDIAnalyzerSettings> mSettings;
    std::unique_ptr<UPDIAnalyzerResults> mResults;
    AnalyzerChannelData* mUPDI;
    //UPDISimulationDataGenerator mSimulationDataGenerator;
    //bool mSimulationInitialized;

    U32 bit_width = 0;

#pragma warning( pop )
};

extern "C" ANALYZER_EXPORT const char* __cdecl GetAnalyzerName();
extern "C" ANALYZER_EXPORT Analyzer* __cdecl CreateAnalyzer();
extern "C" ANALYZER_EXPORT void __cdecl DestroyAnalyzer( Analyzer* analyzer );

#endif // UPDI_ANALYZER_H
