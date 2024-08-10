#pragma once

#include <Analyzer.h>
#include "results.h"
#include "datagenerator.h"

enum updi_state
{
    SYNC,
    SYNCED
};

class updi_settings;

class updi_analyzer : public Analyzer2
{
  public:
    updi_analyzer();
    virtual ~updi_analyzer();
    virtual void SetupResults();
    virtual void WorkerThread();
    bool CorrectWidth( U64 );
    U64 CurrentWidth();
    void Identify(const char* state);
    virtual U32 GenerateSimulationData( U64 newest_sample_requested, U32 sample_rate, SimulationChannelDescriptor** simulation_channels );
    virtual U32 GetMinimumSampleRateHz();

    virtual const char* GetAnalyzerName() const;
    virtual bool NeedsRerun();


#pragma warning( push )
#pragma warning(                                                                                                                           \
    disable : 4251 ) // warning C4251: 'SerialAnalyzer::<...>' : class <...> needs to have dll-interface to be used by clients of class

  protected: // functions
    void ComputeSampleOffsets();

  protected: // vars
    std::unique_ptr<updi_settings> mSettings;
    std::unique_ptr<updi_results> mResults;
    AnalyzerChannelData* channel;

    SerialSimulationDataGenerator mSimulationDataGenerator;
    bool mSimulationInitialized;

    // Serial analysis vars:
    U32 mSampleRateHz;
    U64 RateWidth;
    U64 last_bit;

    std::vector<U32> mSampleOffsets;
    U32 mParityBitOffset;
    U32 mStartOfStopBitOffset;
    U32 mEndOfStopBitOffset;
    AnalyzerChannelData* data;

#pragma warning( pop )
};

extern "C" ANALYZER_EXPORT const char* __cdecl GetAnalyzerName();
extern "C" ANALYZER_EXPORT Analyzer* __cdecl CreateAnalyzer();
extern "C" ANALYZER_EXPORT void __cdecl DestroyAnalyzer( Analyzer* analyzer );
