#ifndef LL_ANALYZER_RESULTS
#define LL_ANALYZER_RESULTS

#include <AnalyzerResults.h>

class ll_analyzer;
class ll_settings;

class ll_results : public AnalyzerResults
{
  public:
    ll_results( ll_analyzer* analyzer, ll_settings* settings );
    virtual ~ll_results();

    virtual void GenerateBubbleText( U64 frame_index, Channel& channel, DisplayBase display_base );
    virtual void GenerateExportFile( const char* file, DisplayBase display_base, U32 export_type_user_id );
    virtual void GenerateFrameTabularText( U64 frame_index, DisplayBase display_base );
    virtual void GeneratePacketTabularText( U64 packet_id, DisplayBase display_base );
    virtual void GenerateTransactionTabularText( U64 transaction_id, DisplayBase display_base );

  protected: // functions
  protected: // vars
    ll_settings* mSettings;
    ll_analyzer* mAnalyzer;
};

#endif // LL_ANALYZER_RESULTS
